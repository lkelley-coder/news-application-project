"""Admin configuration for the custom user model."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin interface for the custom user model and role fields."""
    fieldsets = UserAdmin.fieldsets + (
        (
            "News application",
            {
                "fields": (
                    "role",
                    "publisher_subscriptions",
                    "journalist_subscriptions",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("News application", {"fields": ("role",)}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
