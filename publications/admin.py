"""Admin configuration for publishers."""
from django.contrib import admin

from .models import Publisher


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin interface for publishers and their affiliations."""
    list_display = ("name", "created_at")
    search_fields = ("name",)
    filter_horizontal = ("editors", "journalists")
