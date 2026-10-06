"""Tests for the website's publisher management workflow."""

from django.test import TestCase

from accounts.models import User
from articles.models import Article
from publications.models import Publisher


class PublisherWorkflowTests(TestCase):
    """Editors create and manage publishers; others cannot."""

    def setUp(self):
        """Set up shared fixtures for each test."""
        self.editor = User.objects.create_user(
            "editor", password="pw-12345-long", role=User.EDITOR
        )
        self.other_editor = User.objects.create_user(
            "other-editor", password="pw-12345-long", role=User.EDITOR
        )
        self.journalist = User.objects.create_user(
            "writer", password="pw-12345-long", role=User.JOURNALIST
        )
        self.reader = User.objects.create_user(
            "reader", password="pw-12345-long", role=User.READER
        )

    def test_editor_creates_publisher_and_is_affiliated(self):
        """Editor creates publisher and is affiliated."""
        self.client.force_login(self.editor)

        response = self.client.post(
            "/publishers/create/",
            {
                "name": "Daily Planet",
                "description": "City news",
                "editors": [self.other_editor.pk],
                "journalists": [self.journalist.pk],
            },
        )

        self.assertRedirects(response, "/publishers/")
        publisher = Publisher.objects.get(name="Daily Planet")
        self.assertCountEqual(
            publisher.editors.all(), [self.editor, self.other_editor]
        )
        self.assertEqual(list(publisher.journalists.all()), [self.journalist])

    def test_publisher_requires_an_editor_member(self):
        """Publisher requires an editor member."""
        self.client.force_login(self.editor)

        response = self.client.post(
            "/publishers/create/", {"name": "No Editors", "description": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Publisher.objects.filter(name="No Editors").exists())

    def test_non_editors_cannot_create_publishers(self):
        """Non editors cannot create publishers."""
        for user in (self.journalist, self.reader):
            self.client.force_login(user)
            self.assertEqual(
                self.client.get("/publishers/create/").status_code,
                404,
            )
            self.assertEqual(
                self.client.post(
                    "/publishers/create/",
                    {"name": "X"},
                ).status_code,
                404,
            )
        self.assertFalse(Publisher.objects.exists())

    def test_affiliated_editor_manages_members(self):
        """Affiliated editor manages members."""
        publisher = Publisher.objects.create(name="Tribune")
        publisher.editors.add(self.editor)
        self.client.force_login(self.editor)

        response = self.client.post(
            f"/publishers/{publisher.pk}/edit/",
            {
                "name": "Tribune",
                "description": "Updated",
                "editors": [self.editor.pk],
                "journalists": [self.journalist.pk],
            },
        )

        self.assertRedirects(response, "/publishers/")
        publisher.refresh_from_db()
        self.assertEqual(publisher.description, "Updated")
        self.assertEqual(list(publisher.journalists.all()), [self.journalist])

    def test_unaffiliated_editor_cannot_manage_publisher(self):
        """Unaffiliated editor cannot manage publisher."""
        publisher = Publisher.objects.create(name="Tribune")
        publisher.editors.add(self.editor)
        self.client.force_login(self.other_editor)

        self.assertEqual(
            self.client.get(f"/publishers/{publisher.pk}/edit/").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/publishers/{publisher.pk}/delete/"
            ).status_code,
            404,
        )
        self.assertTrue(Publisher.objects.filter(pk=publisher.pk).exists())

    def test_publisher_with_articles_cannot_be_deleted(self):
        """Publisher with articles cannot be deleted."""
        publisher = Publisher.objects.create(name="Tribune")
        publisher.editors.add(self.editor)
        Article.objects.create(
            title="Story",
            content="Text",
            author=self.journalist,
            publisher=publisher,
        )
        self.client.force_login(self.editor)

        self.client.post(f"/publishers/{publisher.pk}/delete/")

        self.assertTrue(Publisher.objects.filter(pk=publisher.pk).exists())

    def test_empty_publisher_can_be_deleted(self):
        """Empty publisher can be deleted."""
        publisher = Publisher.objects.create(name="Tribune")
        publisher.editors.add(self.editor)
        self.client.force_login(self.editor)

        self.client.post(f"/publishers/{publisher.pk}/delete/")

        self.assertFalse(Publisher.objects.filter(pk=publisher.pk).exists())

    def test_everyone_can_list_publishers_but_only_editors_see_actions(self):
        """Everyone can list publishers but only editors see actions."""
        publisher = Publisher.objects.create(name="Tribune")
        publisher.editors.add(self.editor)

        self.client.force_login(self.journalist)
        response = self.client.get("/publishers/")
        self.assertContains(response, "Tribune")
        self.assertNotContains(response, "Manage members")

        self.client.force_login(self.editor)
        response = self.client.get("/publishers/")
        self.assertContains(response, "Manage members")
        self.assertContains(response, "Create publisher")

    def test_navigation_links_to_publishers_for_editors_and_journalists(self):
        """Navigation links to publishers for editors and journalists."""
        for user in (self.editor, self.journalist):
            self.client.force_login(user)
            self.assertContains(self.client.get("/"), "/publishers/")

    def test_affiliated_journalist_can_then_submit_for_publisher(self):
        """Affiliated journalist can then submit for publisher."""
        publisher = Publisher.objects.create(name="Tribune")
        publisher.editors.add(self.editor)
        publisher.journalists.add(self.journalist)
        self.client.force_login(self.journalist)

        response = self.client.post(
            "/articles/create/",
            {
                "title": "Scoop",
                "content": "Details",
                "publisher": publisher.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Article.objects.get(title="Scoop").publisher,
            publisher,
        )
