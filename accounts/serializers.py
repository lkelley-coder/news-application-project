"""API serializers for user accounts and reader subscriptions."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from publications.models import Publisher

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serialize the current user and any reader subscriptions."""

    publisher_subscriptions = serializers.SerializerMethodField()
    journalist_subscriptions = serializers.SerializerMethodField()

    class Meta:
        """Define the fields exposed on the user profile endpoint."""
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "publisher_subscriptions",
            "journalist_subscriptions",
        ]
        read_only_fields = fields

    def get_publisher_subscriptions(self, user):
        """Return publisher ids for reader accounts."""
        if user.role != User.READER:
            return None
        return list(user.publisher_subscriptions.values_list("id", flat=True))

    def get_journalist_subscriptions(self, user):
        """Return journalist ids for reader accounts."""
        if user.role != User.READER:
            return None
        return list(user.journalist_subscriptions.values_list("id", flat=True))


class ReaderRegistrationSerializer(serializers.ModelSerializer):
    """Create new users through the API registration endpoint."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    role = serializers.ChoiceField(
        choices=User.ROLE_CHOICES,
        default=User.READER,
    )

    class Meta:
        """Define the fields accepted when registering a user."""
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
        ]

    def create(self, validated_data):
        """Create a user with Django's password hashing helpers."""
        return User.objects.create_user(**validated_data)


class ReaderSubscriptionSerializer(serializers.Serializer):
    """Validate reader subscription updates."""

    publishers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Publisher.objects.all(),
        required=False,
    )
    journalists = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role=User.JOURNALIST),
        required=False,
    )
