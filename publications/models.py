"""Database models for publishers and affiliations."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Publisher(models.Model):
    """Group affiliated editors, journalists, and articles."""
    name = models.CharField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="edited_publications",
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="journalist_publications",
        limit_choices_to={"role": "journalist"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate roles for affiliated editors and journalists."""
        super().clean()
        if self.pk and self.editors.exclude(role="editor").exists():
            raise ValidationError(
                {"editors": "Only editors may be affiliated."}
            )
        if self.pk and self.journalists.exclude(role="journalist").exists():
            raise ValidationError(
                {
                    "journalists": (
                        "Only journalists may be affiliated."
                    )
                }
            )

    def __str__(self):
        """Return the publisher name."""
        return self.name
