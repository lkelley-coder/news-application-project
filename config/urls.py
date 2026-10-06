"""Root URL configuration for site pages and API endpoints."""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from articles.views import (
    approve_article_page,
    article_create_page,
    article_delete_page,
    article_detail_page,
    article_edit_page,
    article_workspace,
    editor_review,
    home,
    newsletter_create_page,
    newsletter_delete_page,
    newsletter_detail_page,
    newsletter_edit_page,
    newsletter_list,
    newsletter_workspace,
)
from publications.views import (
    publisher_create_page,
    publisher_delete_page,
    publisher_edit_page,
    publisher_list,
)
from accounts.views import (
    reader_registration_page,
    reader_subscriptions_page,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("newsletters/", newsletter_list, name="newsletter-list"),
    path(
        "newsletters/create/",
        newsletter_create_page,
        name="newsletter-create",
    ),
    path(
        "newsletters/manage/",
        newsletter_workspace,
        name="newsletter-workspace",
    ),
    path(
        "newsletters/<int:pk>/edit/",
        newsletter_edit_page,
        name="newsletter-edit",
    ),
    path(
        "newsletters/<int:pk>/delete/",
        newsletter_delete_page,
        name="newsletter-delete",
    ),
    path(
        "newsletters/<int:pk>/",
        newsletter_detail_page,
        name="newsletter-detail",
    ),
    path("articles/create/", article_create_page, name="article-create"),
    path("articles/manage/", article_workspace, name="article-workspace"),
    path("articles/<int:pk>/edit/", article_edit_page, name="article-edit"),
    path(
        "articles/<int:pk>/delete/",
        article_delete_page,
        name="article-delete",
    ),
    path("articles/<int:pk>/", article_detail_page, name="article-detail"),
    path(
        "subscriptions/",
        reader_subscriptions_page,
        name="reader-subscriptions",
    ),
    path("publishers/", publisher_list, name="publisher-list"),
    path(
        "publishers/create/",
        publisher_create_page,
        name="publisher-create",
    ),
    path(
        "publishers/<int:pk>/edit/",
        publisher_edit_page,
        name="publisher-edit",
    ),
    path(
        "publishers/<int:pk>/delete/",
        publisher_delete_page,
        name="publisher-delete",
    ),
    path("editor/review/", editor_review, name="editor-review"),
    path(
        "editor/articles/<int:pk>/approve/",
        approve_article_page,
        name="approve-article-page",
    ),
    path("accounts/register/", reader_registration_page, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/accounts/", include("accounts.urls")),
    path("api/", include("articles.urls")),
]
