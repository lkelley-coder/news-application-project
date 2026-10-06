"""Service helpers for article approval side effects."""
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from accounts.models import User


def article_subscribers(article):
    """Return active readers subscribed to the author or publisher."""
    # Readers may subscribe to a publisher, a journalist, or both.
    subscription_filter = Q()
    if article.publisher_id:
        subscription_filter |= Q(publisher_subscriptions__articles=article)
    if article.author_id:
        subscription_filter |= Q(journalist_subscriptions=article.author)
    if not subscription_filter:
        return User.objects.none()
    return (
        User.objects.filter(
            role=User.READER,
            is_active=True,
        )
        .filter(subscription_filter)
        .exclude(email="")
        .distinct()
    )


def notify_subscribers(article):
    """Email subscribers and return the number of delivered messages."""
    recipients = list(
        article_subscribers(article).values_list("email", flat=True)
    )
    if not recipients:
        return 0

    return send_mail(
        subject=f"New article: {article.title}",
        message=(
            f"{article.title}\n\n{article.content}\n\n"
            "You received this email because you subscribe to this journalist "
            "or publication."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False,
    )


def log_approved_article(article):
    """Post approval metadata to the configured internal API endpoint."""
    payload = {
        "article_id": article.pk,
        "title": article.title,
        "author": article.author.username if article.author_id else None,
        "publisher": article.publisher.name if article.publisher_id else None,
        "approved": article.approved,
        "approved_at": article.approved_at.isoformat(),
    }
    response = requests.post(
        settings.APPROVED_ARTICLES_API_URL,
        json=payload,
        headers={"X-Internal-API-Key": settings.INTERNAL_API_KEY},
        timeout=settings.APPROVED_API_TIMEOUT,
    )
    response.raise_for_status()


def approve_article(article, editor):
    """Save approval, log it internally, and notify subscribers.

    The approval is persisted before either integration runs. Integration
    errors propagate to the caller without reverting the approval.
    """
    article.approved = True
    article.approved_by = editor
    article.approved_at = timezone.now()
    article.save(
        update_fields=["approved", "approved_by", "approved_at", "updated_at"]
    )

    # The approval flow persists the decision first, then records it through
    # the internal API, and finally sends subscriber email notifications.
    log_approved_article(article)
    return notify_subscribers(article)
