"""Database models for articles, newsletters, and approval logs."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Article(models.Model):
    """A journalist's news article, optionally tied to a publisher."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="articles",
        null=True,
        blank=True,
        limit_choices_to={"role": "journalist"},
    )
    publisher = models.ForeignKey(
        "publications.Publisher",
        on_delete=models.PROTECT,
        related_name="articles",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_articles",
        null=True,
        blank=True,
    )

    class Meta:
        """Apply default ordering and integrity constraints for articles."""
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=Q(author__isnull=False) | Q(publisher__isnull=False),
                name="article_has_author_or_publisher",
            )
        ]

    def clean(self):
        """Validate that an assigned article author is a journalist."""
        super().clean()
        if self.author and self.author.role != "journalist":
            raise ValidationError(
                {"author": "Article authors must be journalists."}
            )

    def __str__(self):
        """Return the article title."""
        return self.title


class Newsletter(models.Model):
    """A curated newsletter containing approved articles."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="newsletters",
        limit_choices_to={"role": "journalist"},
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters",
    )

    class Meta:
        """Apply default ordering for newsletters."""
        ordering = ["-created_at"]

    def clean(self):
        """Validate that an assigned newsletter author is a journalist."""
        super().clean()
        if self.author_id and self.author.role != "journalist":
            raise ValidationError(
                {"author": "Newsletter authors must be journalists."}
            )

    def __str__(self):
        """Return the newsletter title."""
        return self.title


class ApprovedArticleLog(models.Model):
    """An audit record for an approved article."""
    article = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        related_name="approval_log",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField()

    class Meta:
        """Apply default ordering for approval log entries."""
        ordering = ["-approved_at"]

    def __str__(self):
        """Return a readable label for the approval log entry."""
        return f"Approval log: {self.article.title}"
