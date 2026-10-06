"""Forms for creating and managing publishers on the website."""

from django import forms

from accounts.models import User

from .models import Publisher


class PublisherForm(forms.ModelForm):
    """Create or edit publishers and their editors and journalists."""

    class Meta:
        """Define the fields available on the publisher form."""
        model = Publisher
        fields = ["name", "description", "editors", "journalists"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "What does this publication cover?",
                }
            ),
            "editors": forms.CheckboxSelectMultiple,
            "journalists": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        """Limit affiliations to editor and journalist accounts."""
        super().__init__(*args, **kwargs)
        # Only accounts with the matching role may be affiliated.
        self.fields["editors"].queryset = User.objects.filter(
            role=User.EDITOR
        ).order_by("username")
        self.fields["journalists"].queryset = User.objects.filter(
            role=User.JOURNALIST
        ).order_by("username")
        self.fields["editors"].required = True
        self.fields["editors"].help_text = (
            "Editors who can manage this publisher. At least one is required."
        )
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.setdefault("class", "form-control")
