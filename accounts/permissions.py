"""REST framework permission helpers for role-based access."""
from rest_framework.permissions import BasePermission

from .models import User


def user_has_role(user, role):
    """Check a user's role, matching group membership, or superuser status."""
    group_name = {
        User.READER: "Reader",
        User.EDITOR: "Editor",
        User.JOURNALIST: "Journalist",
    }[role]
    return (
        user.is_authenticated
        # Role, group membership, and superuser access all satisfy the check.
        and (
            user.role == role
            or user.groups.filter(name=group_name).exists()
            or user.is_superuser
        )
    )


class IsJournalist(BasePermission):
    """Allow access only to journalists."""

    def has_permission(self, request, view):
        """Check whether the request user may access this view."""
        return user_has_role(request.user, User.JOURNALIST)


class IsEditorOrJournalist(BasePermission):
    """Allow access to editors and journalists, including superusers."""

    def has_permission(self, request, view):
        """Check whether the request user may edit or submit content."""
        return (
            user_has_role(request.user, User.EDITOR)
            or user_has_role(request.user, User.JOURNALIST)
        )


class IsEditor(BasePermission):
    """Allow access only to editors."""

    def has_permission(self, request, view):
        """Return whether the request user may access this editor-only view."""
        return user_has_role(request.user, User.EDITOR)


class IsReader(BasePermission):
    """Allow access only to readers."""

    def has_permission(self, request, view):
        """Return whether the request user may access this reader-only view."""
        return user_has_role(request.user, User.READER)


class IsInternalAPIRequest(BasePermission):
    """Restrict endpoint access to callers with the internal API key."""

    def has_permission(self, request, view):
        """Check whether the request includes the internal API key."""
        from django.conf import settings
        from django.utils.crypto import constant_time_compare

        supplied_key = request.headers.get("X-Internal-API-Key", "")
        # Compare the shared key in constant time because this endpoint is used
        # only by the internal approval logger.
        return bool(supplied_key) and constant_time_compare(
            supplied_key,
            settings.INTERNAL_API_KEY,
        )
