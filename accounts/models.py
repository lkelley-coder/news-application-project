"""Database models for users and reader subscriptions."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with application roles and reader subscriptions."""
    READER = "reader"
    EDITOR = "editor"
    JOURNALIST = "journalist"
    ROLE_CHOICES = [
        (READER, "Reader"),
        (EDITOR, "Editor"),
        (JOURNALIST, "Journalist"),
    ]

    role = models.CharField(
        max_length=12,
        choices=ROLE_CHOICES,
        default=READER,
    )
    publisher_subscriptions = models.ManyToManyField(
        "publications.Publisher",
        blank=True,
        related_name="subscribers",
    )
    journalist_subscriptions = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="journalist_subscribers",
        limit_choices_to={"role": JOURNALIST},
    )

    @property
    def reader_publisher_subscriptions(self):
        """Return a reader's publisher subscriptions when applicable."""
        if self.role != self.READER:
            return None
        return self.publisher_subscriptions.all()

    @property
    def reader_journalist_subscriptions(self):
        """Return a reader's journalist subscriptions when applicable."""
        if self.role != self.READER:
            return None
        return self.journalist_subscriptions.all()

    @property
    def is_reader(self):
        """Return whether the user should be treated as a reader."""
        return (
            self.role == self.READER
            or self.groups.filter(name="Reader").exists()
        )

    @property
    def is_editor(self):
        """Return whether the user should be treated as an editor."""
        return (
            self.role == self.EDITOR
            or self.groups.filter(name="Editor").exists()
            or self.is_superuser
        )

    @property
    def is_journalist(self):
        """Return whether the user should be treated as a journalist."""
        return (
            self.role == self.JOURNALIST
            or self.groups.filter(name="Journalist").exists()
        )

    def __str__(self):
        """Return the full name when available, otherwise the username."""
        return self.get_full_name() or self.username
