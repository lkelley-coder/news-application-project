"""API routes for article, newsletter, and approval endpoints."""
from django.urls import path

from .views import (
    ApprovedArticleEndpoint,
    ArticleApprovalView,
    ArticleDetailView,
    ArticleListCreateView,
    NewsletterDetailView,
    NewsletterListCreateView,
    PublisherListView,
    SubscribedArticlesView,
)

urlpatterns = [
    path(
        "articles/subscribed/",
        SubscribedArticlesView.as_view(),
        name="api-subscribed-articles",
    ),
    path("articles/", ArticleListCreateView.as_view(), name="api-articles"),
    path(
        "articles/<int:pk>/approve/",
        ArticleApprovalView.as_view(),
        name="api-article-approve",
    ),
    path(
        "articles/<int:pk>/",
        ArticleDetailView.as_view(),
        name="api-article-detail",
    ),
    path(
        "newsletters/",
        NewsletterListCreateView.as_view(),
        name="api-newsletters",
    ),
    path(
        "newsletters/<int:pk>/",
        NewsletterDetailView.as_view(),
        name="api-newsletter-detail",
    ),
    path("publishers/", PublisherListView.as_view(), name="api-publishers"),
    path("approved/", ApprovedArticleEndpoint.as_view(), name="api-approved"),
]
