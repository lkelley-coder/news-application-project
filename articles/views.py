"""Website and API views for articles, newsletters, and approvals."""
import smtplib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from requests import RequestException
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import (
    IsEditor,
    IsEditorOrJournalist,
    IsInternalAPIRequest,
    IsJournalist,
    user_has_role,
)
from publications.models import Publisher
from publications.serializers import PublisherSerializer

from .models import Article, ApprovedArticleLog, Newsletter
from .forms import ArticleForm, NewsletterForm
from .serializers import ArticleSerializer, NewsletterSerializer
from .services import approve_article


def articles_for_reader(user):
    """Return articles matching the user's subscriptions."""
    # Readers should see articles from any subscribed publisher or journalist.
    subscription_filter = Q()
    if user.publisher_subscriptions.exists():
        subscription_filter |= Q(
            publisher__in=user.publisher_subscriptions.all()
        )
    if user.journalist_subscriptions.exists():
        subscription_filter |= Q(
            author__in=user.journalist_subscriptions.all()
        )
    if not subscription_filter:
        return Article.objects.none()
    return Article.objects.filter(subscription_filter)


class ArticleListCreateView(generics.ListCreateAPIView):
    """List approved articles and let journalists create new ones."""
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Require journalist access when creating an article."""
        permission_classes = [permissions.IsAuthenticated]
        if self.request.method == "POST":
            permission_classes.append(IsJournalist)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Return approved articles visible to the authenticated user."""
        queryset = Article.objects.filter(approved=True)
        if user_has_role(self.request.user, User.READER):
            queryset = queryset.filter(
                pk__in=articles_for_reader(self.request.user).values("pk")
            )
        return queryset.select_related(
            "author",
            "publisher",
            "approved_by",
        )

    def perform_create(self, serializer):
        """Save a new article for the authenticated journalist."""
        serializer.save(author=self.request.user)


class SubscribedArticlesView(generics.ListAPIView):
    """List approved articles matching the current reader's subscriptions."""
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return the subscribed article feed for the authenticated reader."""
        if not user_has_role(self.request.user, User.READER):
            raise PermissionDenied(
                "Only readers can view subscribed articles."
            )
        return (
            articles_for_reader(self.request.user)
            .filter(approved=True)
            .select_related("author", "publisher", "approved_by")
            .distinct()
        )


class ArticleDetailView(APIView):
    """Retrieve, update, or delete a single article with access checks."""
    permission_classes = [permissions.IsAuthenticated]

    def get_article(self, request, pk, write=False):
        """Return an article after enforcing read or write access rules."""
        article = get_object_or_404(
            Article.objects.select_related(
                "author",
                "publisher",
                "approved_by",
            ),
            pk=pk,
        )
        is_editor = user_has_role(request.user, User.EDITOR)
        is_owner = article.author_id == request.user.pk
        is_journalist = user_has_role(request.user, User.JOURNALIST)

        # Editors can manage any article; journalists can manage only
        # their own submissions.
        if write and not (is_editor or (is_journalist and is_owner)):
            raise PermissionDenied(
                "Only an editor or the article's journalist "
                "may change it."
            )
        if (
            not write
            and user_has_role(request.user, User.READER)
            and not articles_for_reader(request.user)
            .filter(pk=article.pk)
            .exists()
        ):
            raise NotFound("Article not found.")
        if not write and not article.approved and not (is_editor or is_owner):
            raise NotFound("Article not found.")
        return article

    def get(self, request, pk):
        """Return one article."""
        article = self.get_article(request, pk)
        return Response(ArticleSerializer(article).data)

    def put(self, request, pk):
        """Replace an article."""
        return self.update(request, pk, partial=False)

    def patch(self, request, pk):
        """Partially update an article."""
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial):
        """Validate and save article changes."""
        article = self.get_article(request, pk, write=True)
        serializer = ArticleSerializer(
            article,
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete an article the requester may manage."""
        article = self.get_article(request, pk, write=True)
        article.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ArticleApprovalView(APIView):
    """Approve an article through the API."""
    permission_classes = [permissions.IsAuthenticated, IsEditor]

    def post(self, request, pk):
        """Approve an article and trigger downstream integrations."""
        article = get_object_or_404(Article, pk=pk)
        try:
            email_count = approve_article(article, request.user)
        except RequestException as error:
            return Response(
                {"detail": f"Approval saved, but the API log failed: {error}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except smtplib.SMTPException as error:
            return Response(
                {
                    "detail": (
                        "Approval saved, but subscriber email failed: "
                        f"{error}"
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"status": "approved", "emails_sent": email_count},
            status=status.HTTP_200_OK,
        )


class NewsletterListCreateView(generics.ListCreateAPIView):
    """List newsletters and let editors or journalists create them."""
    serializer_class = NewsletterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return newsletters that contain approved articles."""
        return (
            Newsletter.objects.filter(articles__approved=True)
            .select_related("author")
            .prefetch_related("articles")
            .distinct()
        )

    def get_permissions(self):
        """Require editor or journalist access when creating a newsletter."""
        permission_classes = [permissions.IsAuthenticated]
        if self.request.method == "POST":
            permission_classes.append(IsEditorOrJournalist)
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Save a newsletter for the current journalist or selected author."""
        if user_has_role(self.request.user, User.JOURNALIST):
            serializer.save(author=self.request.user)
        else:
            serializer.save()


class NewsletterDetailView(APIView):
    """Retrieve, update, or delete a single newsletter with access checks."""
    permission_classes = [permissions.IsAuthenticated]

    def get_newsletter(self, request, pk, write=False):
        """Return a newsletter after enforcing read or write access rules."""
        newsletter = get_object_or_404(
            Newsletter.objects.select_related("author").prefetch_related(
                "articles"
            ),
            pk=pk,
        )
        is_editor = user_has_role(request.user, User.EDITOR)
        is_owner = newsletter.author_id == request.user.pk
        is_journalist = user_has_role(request.user, User.JOURNALIST)
        # Editors can manage any newsletter; journalists can manage only
        # their own newsletters.
        if write and not (is_editor or (is_journalist and is_owner)):
            raise PermissionDenied(
                "Only an editor or the newsletter's journalist "
                "may change it."
            )
        if not write and not (
            newsletter.articles.filter(approved=True).exists()
            or is_editor
            or is_owner
        ):
            raise NotFound("Newsletter not found.")
        return newsletter

    def get(self, request, pk):
        """Return one newsletter."""
        newsletter = self.get_newsletter(request, pk)
        return Response(NewsletterSerializer(newsletter).data)

    def put(self, request, pk):
        """Replace a newsletter."""
        return self.update(request, pk, partial=False)

    def patch(self, request, pk):
        """Partially update a newsletter."""
        return self.update(request, pk, partial=True)

    def update(self, request, pk, partial):
        """Validate and save newsletter changes."""
        newsletter = self.get_newsletter(request, pk, write=True)
        serializer = NewsletterSerializer(
            newsletter,
            data=request.data,
            partial=partial,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete a newsletter the requester may manage."""
        newsletter = self.get_newsletter(request, pk, write=True)
        newsletter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublisherListView(generics.ListAPIView):
    """List publishers for authenticated users."""
    queryset = Publisher.objects.all().order_by("name")
    serializer_class = PublisherSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApprovedArticleEndpoint(APIView):
    """Expose approved-article logging and reporting endpoints."""

    def get_permissions(self):
        """Require the API key for writes and editor access for reads."""
        if self.request.method == "POST":
            return [IsInternalAPIRequest()]
        return [permissions.IsAuthenticated(), IsEditor()]

    def get(self, request):
        """Return the approved article audit log."""
        logs = ApprovedArticleLog.objects.select_related(
            "article",
            "approved_by",
        )
        results = [
            {
                "article_id": log.article_id,
                "title": log.article.title,
                "approved_by": (
                    log.approved_by.username if log.approved_by_id else None
                ),
                "approved_at": log.approved_at,
            }
            for log in logs
        ]
        return Response(results)

    def post(self, request):
        """Create or update an approval log entry for an approved article."""
        try:
            article_id = int(request.data.get("article_id"))
        except (TypeError, ValueError):
            return Response(
                {"article_id": "A positive integer is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if article_id < 1:
            return Response(
                {"article_id": "A positive integer is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        article = get_object_or_404(
            Article.objects.select_related("approved_by"),
            pk=article_id,
        )
        if not article.approved:
            return Response(
                {"detail": "Only approved articles can be logged."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log, _ = ApprovedArticleLog.objects.update_or_create(
            article=article,
            defaults={
                "approved_by": article.approved_by,
                "approved_at": article.approved_at or timezone.now(),
            },
        )
        return Response(
            {"article_id": log.article_id, "logged": True},
            status=status.HTTP_201_CREATED,
        )


@login_required
def home(request):
    """Render the home page with approved articles visible to the user."""
    articles = Article.objects.filter(approved=True)
    if request.user.is_reader:
        articles = articles.filter(
            pk__in=articles_for_reader(request.user).values("pk")
        )
    articles = articles.select_related(
        "author",
        "publisher",
    )
    return render(request, "articles/home.html", {"articles": articles})


@login_required
def newsletter_list(request):
    """Render the newsletter listing page."""
    newsletters = (
        Newsletter.objects.filter(articles__approved=True)
        .select_related("author")
        .prefetch_related("articles")
        .distinct()
    )
    return render(
        request,
        "articles/newsletters.html",
        {"newsletters": newsletters},
    )


@login_required
def article_workspace(request):
    """Render the article management workspace for journalists and editors."""
    if request.user.is_journalist and not request.user.is_editor:
        articles = Article.objects.filter(author=request.user)
        page_title = "My articles"
        workspace_role = "journalist"
    elif request.user.is_editor:
        articles = Article.objects.all()
        page_title = "Manage articles"
        workspace_role = "editor"
    else:
        raise Http404
    articles = articles.select_related("author", "publisher").order_by(
        "-created_at"
    )
    return render(
        request,
        "articles/workspace.html",
        {
            "articles": articles,
            "page_title": page_title,
            "kind": "article",
            "workspace_role": workspace_role,
        },
    )


@login_required
def article_create_page(request):
    """Render and process the website article creation form."""
    if not request.user.is_journalist:
        raise Http404
    form = ArticleForm(
        request.POST if request.method == "POST" else None,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        article = form.save(commit=False)
        article.author = request.user
        article.save()
        messages.success(
            request,
            "Article submitted. It will be published after editor approval.",
        )
        return redirect("article-workspace")
    return render(
        request,
        "articles/form.html",
        {
            "form": form,
            "page_title": "Write an article",
            "submit_label": "Submit for review",
        },
    )


@login_required
def article_edit_page(request, pk):
    """Render and process the website article editing form."""
    article = get_object_or_404(Article, pk=pk)
    if not (
        request.user.is_editor
        or (
            request.user.is_journalist
            and article.author_id == request.user.pk
        )
    ):
        raise Http404
    form = ArticleForm(
        request.POST or None,
        instance=article,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Article changes saved.")
        return redirect("article-workspace")
    return render(
        request,
        "articles/form.html",
        {
            "form": form,
            "page_title": "Edit article",
            "submit_label": "Save changes",
            "cancel_url": "article-workspace",
        },
    )


@login_required
@require_POST
def article_delete_page(request, pk):
    """Delete an article from the website workflow."""
    article = get_object_or_404(Article, pk=pk)
    if not (
        request.user.is_editor
        or (
            request.user.is_journalist
            and article.author_id == request.user.pk
        )
    ):
        raise Http404
    article.delete()
    messages.success(request, "Article deleted.")
    return redirect("article-workspace")


@login_required
def article_detail_page(request, pk):
    """Render a single article when the user is allowed to view it."""
    article = get_object_or_404(
        Article.objects.select_related("author", "publisher"),
        pk=pk,
    )
    can_manage = request.user.is_editor or (
        request.user.is_journalist and article.author_id == request.user.pk
    )
    if not article.approved and not can_manage:
        raise Http404
    if (
        article.approved
        # Readers may open approved articles only when they match a current
        # publisher or journalist subscription.
        and request.user.is_reader
        and not articles_for_reader(request.user).filter(
            pk=article.pk
        ).exists()
    ):
        raise Http404
    return render(
        request,
        "articles/detail.html",
        {"article": article, "can_manage": can_manage},
    )


@login_required
def newsletter_workspace(request):
    """Render the newsletter workspace for journalists and editors."""
    if request.user.is_journalist and not request.user.is_editor:
        newsletters = Newsletter.objects.filter(author=request.user)
        page_title = "My newsletters"
        workspace_role = "journalist"
    elif request.user.is_editor:
        newsletters = Newsletter.objects.all()
        page_title = "Manage newsletters"
        workspace_role = "editor"
    else:
        raise Http404
    newsletters = newsletters.select_related("author").prefetch_related(
        "articles"
    )
    return render(
        request,
        "articles/workspace.html",
        {
            "newsletters": newsletters,
            "page_title": page_title,
            "kind": "newsletter",
            "workspace_role": workspace_role,
        },
    )


@login_required
def newsletter_create_page(request):
    """Render and process the website newsletter creation form."""
    if not (request.user.is_journalist or request.user.is_editor):
        raise Http404
    form = NewsletterForm(
        request.POST if request.method == "POST" else None,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        newsletter = form.save(commit=False)
        if request.user.is_journalist and not request.user.is_editor:
            newsletter.author = request.user
        newsletter.save()
        form.save_m2m()
        messages.success(request, "Newsletter created.")
        return redirect("newsletter-workspace")
    return render(
        request,
        "articles/form.html",
        {
            "form": form,
            "page_title": "Create a newsletter",
            "submit_label": "Create newsletter",
        },
    )


@login_required
def newsletter_edit_page(request, pk):
    """Render and process the website newsletter editing form."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if not (
        request.user.is_editor
        or (
            request.user.is_journalist
            and newsletter.author_id == request.user.pk
        )
    ):
        raise Http404
    form = NewsletterForm(
        request.POST or None,
        instance=newsletter,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        updated_newsletter = form.save(commit=False)
        if request.user.is_journalist and not request.user.is_editor:
            updated_newsletter.author = request.user
        updated_newsletter.save()
        form.save_m2m()
        messages.success(request, "Newsletter changes saved.")
        return redirect("newsletter-workspace")
    return render(
        request,
        "articles/form.html",
        {
            "form": form,
            "page_title": "Edit newsletter",
            "submit_label": "Save changes",
            "cancel_url": "newsletter-workspace",
        },
    )


@login_required
@require_POST
def newsletter_delete_page(request, pk):
    """Delete a newsletter from the website workflow."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if not (
        request.user.is_editor
        or (
            request.user.is_journalist
            and newsletter.author_id == request.user.pk
        )
    ):
        raise Http404
    newsletter.delete()
    messages.success(request, "Newsletter deleted.")
    return redirect("newsletter-workspace")


@login_required
def newsletter_detail_page(request, pk):
    """Render a single newsletter when the user is allowed to view it."""
    newsletter = get_object_or_404(
        Newsletter.objects.select_related("author").prefetch_related(
            "articles"
        ),
        pk=pk,
    )
    can_manage = request.user.is_editor or (
        request.user.is_journalist and newsletter.author_id == request.user.pk
    )
    if not (
        newsletter.articles.filter(approved=True).exists()
        or can_manage
    ):
        raise Http404
    return render(
        request,
        "articles/newsletter_detail.html",
        {"newsletter": newsletter, "can_manage": can_manage},
    )


@login_required
def editor_review(request):
    """Render the editor queue of unapproved articles."""
    if not user_has_role(request.user, User.EDITOR):
        return HttpResponseForbidden("Editor access is required.")
    pending_articles = Article.objects.filter(approved=False).select_related(
        "author",
        "publisher",
    )
    return render(
        request,
        "articles/editor_review.html",
        {"articles": pending_articles},
    )


@login_required
@require_POST
def approve_article_page(request, pk):
    """Approve an article from the website review queue."""
    if not user_has_role(request.user, User.EDITOR):
        return HttpResponseForbidden("Editor access is required.")
    article = get_object_or_404(Article, pk=pk)
    try:
        approve_article(article, request.user)
    except RequestException as error:
        messages.error(
            request,
            f"Approval saved, but API logging failed: {error}",
        )
    except smtplib.SMTPException as error:
        messages.error(
            request,
            f"Approval saved, but subscriber email failed: {error}",
        )
    else:
        messages.success(request, "Article approved and subscribers notified.")
    return redirect("editor-review")
