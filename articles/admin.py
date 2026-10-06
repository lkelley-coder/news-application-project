"""Admin configuration for articles, newsletters, and approval logs."""
from django.contrib import admin

from .models import Article, ApprovedArticleLog, Newsletter


class ArticleAdmin(admin.ModelAdmin):
    """Admin interface for reviewing article records."""

    list_display = ("title", "author", "created_at", "approved")
    list_filter = ("approved", "created_at")
    search_fields = ("title", "content")
    ordering = ("-created_at",)


admin.site.register(Article, ArticleAdmin)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin interface for newsletters and their article selections."""

    list_display = ("title", "author", "created_at")
    search_fields = ("title", "description", "author__username")
    filter_horizontal = ("articles",)


@admin.register(ApprovedArticleLog)
class ApprovedArticleLogAdmin(admin.ModelAdmin):
    """Read-only admin interface for approved article audit entries."""

    list_display = ("article", "approved_by", "approved_at")
    readonly_fields = ("article", "approved_by", "approved_at")

    def has_add_permission(self, request):
        """Prevent manual creation of approval log entries."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent manual editing of approval log entries."""
        return False
