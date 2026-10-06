"""API serializers for articles and newsletters."""
from rest_framework import serializers

from accounts.models import User
from accounts.permissions import user_has_role
from .models import Article, Newsletter


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize article data for the API."""

    author_name = serializers.CharField(
        source="author.username",
        read_only=True,
    )
    publisher_name = serializers.CharField(
        source="publisher.name",
        read_only=True,
    )
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    approved = serializers.BooleanField(read_only=True)
    approved_by = serializers.PrimaryKeyRelatedField(read_only=True)
    approved_at = serializers.DateTimeField(read_only=True)

    class Meta:
        """Define the API fields and read-only article attributes."""
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "author_name",
            "publisher",
            "publisher_name",
            "created_at",
            "updated_at",
            "approved",
            "approved_at",
            "approved_by",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "approved",
            "approved_at",
            "approved_by",
        ]

    def validate(self, attrs):
        """Ensure journalists only submit content for affiliated publishers."""
        request = self.context.get("request")
        publisher = attrs.get(
            "publisher",
            self.instance.publisher if self.instance else None,
        )
        if (
            request
            and publisher
            and user_has_role(request.user, User.JOURNALIST)
            and not publisher.journalists.filter(pk=request.user.pk).exists()
        ):
            raise serializers.ValidationError(
                {
                    "publisher": (
                        "You must be affiliated with this publisher "
                        "to submit its content."
                    )
                }
            )
        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize newsletter data for the API."""

    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.JOURNALIST),
        required=False,
    )
    author_name = serializers.CharField(
        source="author.username",
        read_only=True,
    )
    articles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Article.objects.filter(approved=True),
        required=False,
    )

    class Meta:
        """Define the API fields and read-only newsletter attributes."""
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "author_name",
            "articles",
        ]
        read_only_fields = ["id", "created_at"]

    def __init__(self, *args, **kwargs):
        """Make the author field read-only for non-editors."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and not user_has_role(request.user, User.EDITOR):
            self.fields["author"].read_only = True

    def validate(self, attrs):
        """Set the author based on the requester's role."""
        request = self.context.get("request")
        if self.instance is None and request:
            if user_has_role(request.user, User.JOURNALIST):
                attrs["author"] = request.user
            elif "author" not in attrs:
                raise serializers.ValidationError(
                    {"author": "Editors must select a journalist author."}
                )
        return attrs

    def to_representation(self, instance):
        """Return only approved article ids in newsletter output."""
        data = super().to_representation(instance)
        data["articles"] = list(
            instance.articles.filter(approved=True).values_list(
                "id",
                flat=True,
            )
        )
        return data
