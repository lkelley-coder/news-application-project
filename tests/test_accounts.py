"""Tests for account registration, roles, and subscription pages."""

from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.models import User


class AccountTests(TestCase):
    """Test account registration, authorization, and navigation behaviors."""
    def test_api_registration_defaults_to_reader(self):
        """API registration defaults to reader."""
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "new-reader",
                "email": "reader@example.com",
                "password": "a-strong-password-123",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            User.objects.get(username="new-reader").role,
            User.READER,
        )

    def test_api_registration_accepts_a_chosen_role(self):
        """API registration accepts a chosen role."""
        for role in (User.JOURNALIST, User.EDITOR):
            response = self.client.post(
                "/api/accounts/register/",
                {
                    "username": f"new-{role}",
                    "email": f"{role}@example.com",
                    "password": "a-strong-password-123",
                    "role": role,
                },
            )

            self.assertEqual(response.status_code, 201)
            user = User.objects.get(username=f"new-{role}")
            self.assertEqual(user.role, role)
            self.assertTrue(user.groups.filter(name=role.title()).exists())

    def test_api_registration_rejects_an_unknown_role(self):
        """API registration rejects an unknown role."""
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "bad-role",
                "password": "a-strong-password-123",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="bad-role").exists())

    def test_api_token_authentication(self):
        """API token authentication."""
        User.objects.create_user(
            username="token-reader",
            password="a-strong-password-123",
            role=User.READER,
        )

        response = self.client.post(
            "/api/token/",
            {
                "username": "token-reader",
                "password": "a-strong-password-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["token"])

    def test_role_groups_are_assigned(self):
        """Role groups are assigned."""
        journalist = User.objects.create_user(
            username="group-journalist",
            password="a-strong-password-123",
            role=User.JOURNALIST,
        )

        self.assertTrue(journalist.groups.filter(name="Journalist").exists())

    def test_group_assignment_sets_and_preserves_role(self):
        """Group assignment sets and preserves role."""
        reader = User.objects.create_user(
            username="group-assigned-editor",
            password="a-strong-password-123",
            role=User.READER,
        )
        editor_group = Group.objects.get(name="Editor")

        reader.groups.add(editor_group)
        reader.refresh_from_db()
        reader.first_name = "Assigned"
        reader.save()
        reader.refresh_from_db()

        self.assertEqual(reader.role, User.EDITOR)
        self.assertTrue(reader.groups.filter(name="Editor").exists())
        self.assertFalse(reader.groups.filter(name="Reader").exists())

    def test_role_groups_only_have_article_and_newsletter_permissions(self):
        """Role groups only have article and newsletter permissions."""
        editor = Group.objects.get(name="Editor")
        reader = Group.objects.get(name="Reader")
        journalist = Group.objects.get(name="Journalist")

        editor_codenames = set(
            editor.permissions.values_list("codename", flat=True)
        )
        reader_codenames = set(
            reader.permissions.values_list("codename", flat=True)
        )
        journalist_models = set(
            journalist.permissions.values_list(
                "content_type__model",
                flat=True,
            )
        )

        self.assertIn("add_newsletter", editor_codenames)
        self.assertNotIn("add_article", editor_codenames)
        self.assertTrue(
            all(name.startswith("view_") for name in reader_codenames)
        )
        self.assertEqual(journalist_models, {"article", "newsletter"})

    def test_journalist_subscription_fields_serialize_as_none(self):
        """Journalist subscription fields serialize as none."""
        journalist = User.objects.create_user(
            username="profile-journalist",
            password="a-strong-password-123",
            role=User.JOURNALIST,
        )
        client = APIClient()
        client.force_authenticate(journalist)

        response = client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["publisher_subscriptions"])
        self.assertIsNone(response.data["journalist_subscriptions"])

    def test_editor_review_page_is_access_controlled(self):
        """Editor review page is access controlled."""
        reader = User.objects.create_user(
            username="page-reader",
            password="a-strong-password-123",
            role=User.READER,
        )
        editor = User.objects.create_user(
            username="page-editor",
            password="a-strong-password-123",
            role=User.EDITOR,
        )

        self.client.force_login(reader)
        self.assertEqual(self.client.get("/editor/review/").status_code, 403)

        self.client.force_login(editor)
        self.assertEqual(self.client.get("/editor/review/").status_code, 200)

    def test_journalist_navigation_links_to_article_and_newsletter_creation(
        self,
    ):
        """Journalist navigation links to article and newsletter creation."""
        journalist = User.objects.create_user(
            username="nav-journalist",
            password="a-strong-password-123",
            role=User.JOURNALIST,
        )
        self.client.force_login(journalist)

        response = self.client.get("/")

        self.assertContains(
            response,
            'href="/articles/create/">Write article</a>',
        )
        self.assertContains(
            response,
            'href="/newsletters/create/">Create newsletter</a>',
        )
        self.assertContains(
            response,
            'href="/articles/manage/">My articles</a>',
        )
        self.assertContains(
            response,
            'href="/newsletters/manage/">My newsletters</a>',
        )
        self.assertNotContains(response, "Editor review")
        self.assertNotContains(response, "Manage articles")

    def test_editor_navigation_links_to_permitted_actions(self):
        """Editor navigation links to permitted actions."""
        editor = User.objects.create_user(
            username="nav-editor",
            password="a-strong-password-123",
            role=User.EDITOR,
        )
        self.client.force_login(editor)

        response = self.client.get("/")

        self.assertContains(
            response,
            'href="/editor/review/">Editor review</a>',
        )
        self.assertContains(
            response,
            'href="/articles/manage/">Manage articles</a>',
        )
        self.assertContains(
            response,
            'href="/newsletters/create/">Create newsletter</a>',
        )
        self.assertContains(
            response,
            'href="/newsletters/manage/">Manage newsletters</a>',
        )
        self.assertNotContains(response, "Write article")

    def test_reader_navigation_does_not_show_creation_links(self):
        """Reader navigation does not show creation links."""
        reader = User.objects.create_user(
            username="nav-reader",
            password="a-strong-password-123",
            role=User.READER,
        )
        self.client.force_login(reader)

        response = self.client.get("/")

        self.assertContains(response, "My subscriptions")
        self.assertNotContains(response, "Write article")
        self.assertNotContains(response, "Create newsletter")
        self.assertNotContains(response, "Manage articles")

    def test_registration_page_creates_account_with_chosen_role(self):
        """Registration page creates account with chosen role."""
        for role in (User.READER, User.JOURNALIST, User.EDITOR):
            response = self.client.post(
                "/accounts/register/",
                {
                    "username": f"html-{role}",
                    "email": f"{role}@example.com",
                    "first_name": "New",
                    "last_name": "Account",
                    "role": role,
                    "password1": "a-strong-password-123",
                    "password2": "a-strong-password-123",
                },
            )

            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                User.objects.get(username=f"html-{role}").role,
                role,
            )

    def test_registration_page_requires_a_valid_role(self):
        """Registration page requires a valid role."""
        response = self.client.post(
            "/accounts/register/",
            {
                "username": "no-role",
                "password1": "a-strong-password-123",
                "password2": "a-strong-password-123",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no-role").exists())

    def test_reader_can_manage_subscriptions_in_the_web_ui(self):
        """Reader can manage subscriptions in the web UI."""
        from publications.models import Publisher

        reader = User.objects.create_user(
            username="subscription-reader",
            password="a-strong-password-123",
            role=User.READER,
        )
        publisher = Publisher.objects.create(name="Web UI Publisher")
        self.client.force_login(reader)

        response = self.client.post(
            "/subscriptions/",
            {"publishers": [publisher.pk]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(reader.publisher_subscriptions.all()),
            [publisher],
        )
