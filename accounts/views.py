"""Website and API views for account registration and subscriptions."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import ReaderRegistrationForm, ReaderSubscriptionForm
from .models import User
from .serializers import (
    ReaderRegistrationSerializer,
    ReaderSubscriptionSerializer,
    UserSerializer,
)


class ReaderRegistrationView(generics.CreateAPIView):
    """Create a user account through the API."""

    serializer_class = ReaderRegistrationSerializer
    permission_classes = [permissions.AllowAny]


@require_http_methods(["GET", "POST"])
def reader_registration_page(request):
    """Render and process the website registration form."""
    if request.user.is_authenticated:
        return redirect("home")
    form = ReaderRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Your reader account is ready. Please sign in.",
        )
        return redirect("login")
    return render(request, "registration/register.html", {"form": form})


@login_required
def reader_subscriptions_page(request):
    """Render and process the website subscription form for readers."""
    # Subscription management is limited to reader accounts.
    if not request.user.is_reader:
        return HttpResponseForbidden("Reader access is required.")

    form = ReaderSubscriptionForm(
        request.POST if request.method == "POST" else None,
        initial={
            "publishers": request.user.publisher_subscriptions.all(),
            "journalists": request.user.journalist_subscriptions.all(),
        },
    )
    if request.method == "POST" and form.is_valid():
        request.user.publisher_subscriptions.set(
            form.cleaned_data["publishers"]
        )
        request.user.journalist_subscriptions.set(
            form.cleaned_data["journalists"]
        )
        messages.success(request, "Your subscriptions have been updated.")
        return redirect("reader-subscriptions")
    return render(
        request,
        "accounts/subscriptions.html",
        {"form": form},
    )


class CurrentUserView(APIView):
    """Return the authenticated user's profile data."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Serialize and return the current user."""
        return Response(UserSerializer(request.user).data)


class CurrentTokenView(APIView):
    """Return or create the authenticated user's API token."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return the current user's token key."""
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({"token": token.key})


class ReaderSubscriptionsView(APIView):
    """Update the authenticated reader's subscriptions through the API."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        """Apply reader subscription changes from a partial update request."""
        # Only readers can manage publisher and journalist subscriptions.
        if request.user.role != User.READER:
            return Response(
                {"detail": "Only readers can manage subscriptions."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ReaderSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if "publishers" in serializer.validated_data:
            request.user.publisher_subscriptions.set(
                serializer.validated_data["publishers"]
            )
        if "journalists" in serializer.validated_data:
            request.user.journalist_subscriptions.set(
                serializer.validated_data["journalists"]
            )
        return Response(UserSerializer(request.user).data)
