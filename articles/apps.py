"""Application configuration for the articles app."""
from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    """Configure the articles application."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "articles"
