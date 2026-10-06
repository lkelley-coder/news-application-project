"""Tests for article, newsletter, approval, and subscription workflows."""

from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from articles.models import Article, ApprovedArticleLog, Newsletter
from publications.models import Publisher


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    INTERNAL_API_KEY="test-internal-key",
)
class NewsAPITests(TestCase):
    """Test article, newsletter, approval, and subscription API workflows."""
    def setUp(self):
        """Set up shared fixtures for each test."""
        self.client = APIClient()
        self.reader = User.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="strong-password-123",
            role=User.READER,
        )
        self.other_reader = User.objects.create_user(
            username="other-reader",
            email="other@example.com",
            password="strong-password-123",
            role=User.READER,
        )
        self.journalist = User.objects.create_user(
            username="journalist",
            email="journalist@example.com",
            password="strong-password-123",
            role=User.JOURNALIST,
        )
        self.other_journalist = User.objects.create_user(
            username="other-journalist",
            password="strong-password-123",
            role=User.JOURNALIST,
        )
        self.editor = User.objects.create_user(
            username="editor",
            password="strong-password-123",
            role=User.EDITOR,
        )
        self.publisher = Publisher.objects.create(name="The Daily Brief")
        self.publisher.journalists.add(self.journalist)
        self.reader.publisher_subscriptions.add(self.publisher)
        self.reader.journalist_subscriptions.add(self.journalist)

        self.publisher_article = Article.objects.create(
            title="A publisher story",
            content="Publisher reporting.",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )
        self.independent_article = Article.objects.create(
            title="An independent story",
            content="Independent reporting.",
            author=self.journalist,
            approved=True,
        )
        self.unrelated_article = Article.objects.create(
            title="An unrelated story",
            content="Not subscribed.",
            author=self.other_journalist,
            approved=True,
        )
        self.pending_article = Article.objects.create(
            title="A pending story",
            content="Not yet published.",
            author=self.journalist,
        )

    def test_article_list_returns_approved_articles_only(self):
        """Article list returns approved articles only."""
        self.client.force_authenticate(self.reader)

        response = self.client.get("/api/articles/")

        self.assertEqual(response.status_code, 200)
        returned_ids = {row["id"] for row in response.data["results"]}
        self.assertIn(self.publisher_article.pk, returned_ids)
        self.assertIn(self.independent_article.pk, returned_ids)
        self.assertNotIn(self.unrelated_article.pk, returned_ids)
        self.assertNotIn(self.pending_article.pk, returned_ids)

    def test_reader_can_retrieve_subscribed_article_only(self):
        """Reader can retrieve subscribed article only."""
        self.client.force_authenticate(self.reader)

        subscribed_response = self.client.get(
            f"/api/articles/{self.publisher_article.pk}/"
        )
        unrelated_response = self.client.get(
            f"/api/articles/{self.unrelated_article.pk}/"
        )

        self.assertEqual(subscribed_response.status_code, 200)
        self.assertEqual(unrelated_response.status_code, 404)

    def test_subscribed_reader_only_gets_publisher_or_journalist_content(self):
        """Subscribed reader only gets publisher or journalist content."""
        self.client.force_authenticate(self.reader)

        response = self.client.get("/api/articles/subscribed/")

        self.assertEqual(response.status_code, 200)
        returned_ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(
            returned_ids,
            {self.publisher_article.pk, self.independent_article.pk},
        )
        self.assertNotIn(self.unrelated_article.pk, returned_ids)
        self.assertNotIn(self.pending_article.pk, returned_ids)

    def test_unauthenticated_api_access_is_rejected(self):
        """Unauthenticated API access is rejected."""
        response = self.client.get("/api/articles/")

        self.assertEqual(response.status_code, 401)

    def test_readers_cannot_create_articles(self):
        """Readers cannot create articles."""
        self.client.force_authenticate(self.reader)

        response = self.client.post(
            "/api/articles/",
            {"title": "Reader submission", "content": "Not permitted."},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalists_can_create_articles(self):
        """Journalists can create articles."""
        self.client.force_authenticate(self.journalist)

        response = self.client.post(
            "/api/articles/",
            {"title": "New report", "content": "Submitted by a journalist."},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(pk=response.data["id"])
        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)

    def test_journalist_can_create_and_edit_article_from_site(self):
        """Journalist can create and edit article from site."""
        self.client.force_login(self.journalist)

        response = self.client.post(
            "/articles/create/",
            {
                "title": "Site-created article",
                "content": "A complete story submitted from the website.",
                "publisher": "",
            },
        )

        self.assertRedirects(response, "/articles/manage/")
        article = Article.objects.get(title="Site-created article")
        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)

        edit_response = self.client.post(
            f"/articles/{article.pk}/edit/",
            {
                "title": "Updated site article",
                "content": "The journalist can revise their submission.",
                "publisher": "",
            },
        )
        self.assertRedirects(edit_response, "/articles/manage/")
        article.refresh_from_db()
        self.assertEqual(article.title, "Updated site article")

    def test_journalist_site_workflow_rejects_other_authors_content(self):
        """Journalist site workflow rejects other authors content."""
        self.client.force_login(self.journalist)

        response = self.client.get(
            f"/articles/{self.unrelated_article.pk}/edit/"
        )

        self.assertEqual(response.status_code, 404)

    def test_reader_cannot_open_journalist_create_page(self):
        """Reader cannot open journalist create page."""
        self.client.force_login(self.reader)

        response = self.client.get("/articles/create/")

        self.assertEqual(response.status_code, 404)

    def test_api_browsable_page_hides_request_console_but_keeps_create_form(
        self,
    ):
        """API browsable page hides request console but keeps create form."""
        self.client.force_authenticate(self.journalist)

        response = self.client.get("/api/articles/", HTTP_ACCEPT="text/html")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '.region[aria-label="request form"]',
        )
        self.assertContains(response, ".request-info")
        self.assertContains(response, ".response-info")
        self.assertContains(response, "display: none !important;")
        self.assertContains(response, 'a[name="raw-tab"]')
        self.assertContains(response, 'id="post-object-form"')
        self.assertContains(response, "Title")
        self.assertContains(response, "Content")

    def test_journalists_cannot_submit_for_unaffiliated_publishers(self):
        """Journalists cannot submit for unaffiliated publishers."""
        unaffiliated_publisher = Publisher.objects.create(
            name="Unaffiliated Publisher"
        )
        self.client.force_authenticate(self.journalist)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "Unauthorized publisher story",
                "content": "This should be rejected.",
                "publisher": unaffiliated_publisher.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_editor_can_approve_article_and_trigger_integrations(self):
        """Editor can approve article and trigger integrations."""
        self.client.force_authenticate(self.editor)
        with (
            patch("articles.services.requests.post") as post_request,
            patch("articles.services.send_mail", return_value=1) as send_mail,
        ):
            response = self.client.post(
                f"/api/articles/{self.pending_article.pk}/approve/"
            )

        self.assertEqual(response.status_code, 200)
        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)
        self.assertEqual(self.pending_article.approved_by, self.editor)
        post_request.assert_called_once()
        self.assertEqual(
            post_request.call_args.kwargs["json"]["article_id"],
            self.pending_article.pk,
        )
        send_mail.assert_called_once()
        self.assertEqual(
            send_mail.call_args.kwargs["recipient_list"],
            [self.reader.email],
        )

    def test_editor_can_approve_from_site_queue(self):
        """Editor can approve from site queue."""
        self.client.force_login(self.editor)
        with (
            patch("articles.services.requests.post"),
            patch("articles.services.send_mail", return_value=1),
        ):
            response = self.client.post(
                f"/editor/articles/{self.pending_article.pk}/approve/"
            )

        self.assertRedirects(response, "/editor/review/")
        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)
        self.assertEqual(self.pending_article.approved_by, self.editor)

    def test_non_editors_cannot_approve(self):
        """Non editors cannot approve."""
        self.client.force_authenticate(self.reader)

        response = self.client.post(
            f"/api/articles/{self.pending_article.pk}/approve/"
        )

        self.assertEqual(response.status_code, 403)
        self.pending_article.refresh_from_db()
        self.assertFalse(self.pending_article.approved)

    def test_editor_can_delete_articles(self):
        """Editor can delete articles."""
        self.client.force_authenticate(self.editor)

        response = self.client.delete(
            f"/api/articles/{self.unrelated_article.pk}/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Article.objects.filter(pk=self.unrelated_article.pk).exists()
        )

    def test_journalist_cannot_edit_another_journalists_article(self):
        """Journalist cannot edit another journalists article."""
        self.client.force_authenticate(self.journalist)

        response = self.client.put(
            f"/api/articles/{self.unrelated_article.pk}/",
            {"title": "Overwritten", "content": "Not allowed."},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalists_can_create_newsletters_with_approved_articles(self):
        """Journalists can create newsletters with approved articles."""
        self.client.force_authenticate(self.journalist)

        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "This week",
                "description": "A selected reading list.",
                "articles": [self.publisher_article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        newsletter = Newsletter.objects.get(pk=response.data["id"])
        self.assertEqual(newsletter.author, self.journalist)
        self.assertEqual(
            list(newsletter.articles.all()),
            [self.publisher_article],
        )

    def test_journalist_can_create_newsletter_from_site(self):
        """Journalist can create newsletter from site."""
        self.client.force_login(self.journalist)

        response = self.client.post(
            "/newsletters/create/",
            {
                "title": "Site newsletter",
                "description": "Our weekly picks.",
                "articles": [self.publisher_article.pk],
            },
        )

        self.assertRedirects(response, "/newsletters/manage/")
        newsletter = Newsletter.objects.get(title="Site newsletter")
        self.assertEqual(newsletter.author, self.journalist)
        self.assertEqual(
            list(newsletter.articles.all()),
            [self.publisher_article],
        )

    def test_editor_can_create_and_manage_newsletter_from_site(self):
        """Editor can create and manage newsletter from site."""
        self.client.force_login(self.editor)

        response = self.client.post(
            "/newsletters/create/",
            {
                "title": "Editor site newsletter",
                "description": "A curated set.",
                "author": self.journalist.pk,
                "articles": [self.publisher_article.pk],
            },
        )

        self.assertRedirects(response, "/newsletters/manage/")
        newsletter = Newsletter.objects.get(title="Editor site newsletter")
        self.assertEqual(newsletter.author, self.journalist)
        edit_response = self.client.post(
            f"/newsletters/{newsletter.pk}/edit/",
            {
                "title": "Updated editor newsletter",
                "description": "Updated curated set.",
                "author": self.journalist.pk,
                "articles": [self.publisher_article.pk],
            },
        )
        self.assertRedirects(edit_response, "/newsletters/manage/")
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.title, "Updated editor newsletter")

        delete_response = self.client.post(
            f"/newsletters/{newsletter.pk}/delete/"
        )
        self.assertRedirects(delete_response, "/newsletters/manage/")
        self.assertFalse(Newsletter.objects.filter(pk=newsletter.pk).exists())

    def test_journalists_cannot_change_newsletter_authorship(self):
        """Journalists cannot change newsletter authorship."""
        newsletter = Newsletter.objects.create(
            title="Original author",
            author=self.journalist,
        )
        self.client.force_authenticate(self.journalist)

        response = self.client.patch(
            f"/api/newsletters/{newsletter.pk}/",
            {"author": self.other_journalist.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.author, self.journalist)

    def test_editor_can_create_newsletter_for_a_journalist(self):
        """Editor can create newsletter for a journalist."""
        self.client.force_authenticate(self.editor)

        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Editor-curated selection",
                "author": self.journalist.pk,
                "articles": [self.publisher_article.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Newsletter.objects.get(pk=response.data["id"]).author,
            self.journalist,
        )

    def test_readers_can_view_but_cannot_create_newsletters(self):
        """Readers can view but cannot create newsletters."""
        newsletter = Newsletter.objects.create(
            title="Reader edition",
            author=self.journalist,
        )
        newsletter.articles.add(self.publisher_article)
        self.client.force_authenticate(self.reader)

        list_response = self.client.get("/api/newsletters/")
        create_response = self.client.post(
            "/api/newsletters/",
            {"title": "Reader newsletter"},
            format="json",
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["results"]), 1)
        self.assertEqual(create_response.status_code, 403)

    def test_approved_endpoint_requires_internal_key_and_logs_article(self):
        """Approved endpoint requires internal key and logs article."""
        response = self.client.post(
            "/api/approved/",
            {"article_id": self.publisher_article.pk},
            format="json",
            HTTP_X_INTERNAL_API_KEY="wrong-key",
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.post(
            "/api/approved/",
            {"article_id": self.publisher_article.pk},
            format="json",
            HTTP_X_INTERNAL_API_KEY="test-internal-key",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ApprovedArticleLog.objects.filter(
                article=self.publisher_article
            ).exists()
        )

    def test_reader_can_update_subscriptions_and_non_reader_cannot(self):
        """Reader can update subscriptions and non reader cannot."""
        response = self.client.patch(
            "/api/accounts/me/subscriptions/",
            {
                "publishers": [self.publisher.pk],
                "journalists": [self.other_journalist.pk],
            },
            format="json",
            HTTP_AUTHORIZATION="",
        )
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(self.reader)
        response = self.client.patch(
            "/api/accounts/me/subscriptions/",
            {
                "publishers": [self.publisher.pk],
                "journalists": [self.other_journalist.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["journalist_subscriptions"],
            [self.other_journalist.pk],
        )

        self.client.force_authenticate(self.journalist)
        denied = self.client.patch(
            "/api/accounts/me/subscriptions/",
            {"publishers": [self.publisher.pk]},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
