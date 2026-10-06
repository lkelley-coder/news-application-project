"""API routes for account registration and profile endpoints."""
from django.urls import path

from .views import (
    CurrentTokenView,
    CurrentUserView,
    ReaderRegistrationView,
    ReaderSubscriptionsView,
)

urlpatterns = [
    path("register/", ReaderRegistrationView.as_view(), name="api-register"),
    path("me/", CurrentUserView.as_view(), name="api-current-user"),
    path(
        "me/subscriptions/",
        ReaderSubscriptionsView.as_view(),
        name="api-reader-subscriptions",
    ),
    path("token/", CurrentTokenView.as_view(), name="api-current-token"),
]
