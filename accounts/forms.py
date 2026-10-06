"""Forms for reader registration and subscription management."""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from publications.models import Publisher

from .models import User


class ReaderSubscriptionForm(forms.Form):
    """Collect publisher and journalist subscriptions for a reader."""
    publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    journalists = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            role=User.JOURNALIST
        ).order_by("username"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


class ReaderRegistrationForm(UserCreationForm):
    """Register a user with one of the supported account roles."""
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial=User.READER,
        help_text="Choose how you will use News 4 U.",
    )

    class Meta:
        """Configure the user fields shown on the registration form."""
        model = User
        fields = ("username", "email", "first_name", "last_name", "role")

    def save(self, commit=True):
        """Persist the user with the selected application role."""
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user
