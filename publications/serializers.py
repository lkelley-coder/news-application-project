"""API serializers for publishers."""
from rest_framework import serializers

from .models import Publisher


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize publishers and their affiliated account ids."""
    editors = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    journalists = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        """Define the fields exposed for publishers."""
        model = Publisher
        fields = ["id", "name", "description", "editors", "journalists"]
