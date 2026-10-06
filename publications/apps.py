"""Application configuration for the publications app."""
from django.apps import AppConfig


class PublicationsConfig(AppConfig):
    """Configure the publications application."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "publications"
