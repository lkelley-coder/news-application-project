"""Forms for creating and editing articles and newsletters."""
from django import forms

from accounts.models import User
from publications.models import Publisher

from .models import Article, Newsletter


class SiteFormMixin:
    """Apply shared widget styling for website forms."""

    def apply_site_widgets(self):
        """Apply the default CSS class to non-checkbox widgets."""
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ArticleForm(SiteFormMixin, forms.ModelForm):
    """Create or edit an article from the website."""

    class Meta:
        """Define the fields available on the article form."""
        model = Article
        fields = ["title", "content", "publisher"]
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 12, "placeholder": "Write your article..."}
            )
        }

    def __init__(self, *args, user, **kwargs):
        """Limit publishers to the user's permitted affiliations."""
        super().__init__(*args, **kwargs)
        self.fields["publisher"].queryset = Publisher.objects.none()
        self.fields["publisher"].required = False
        if user.is_editor:
            self.fields["publisher"].queryset = (
                Publisher.objects.all().order_by("name")
            )
        elif user.is_journalist:
            self.fields["publisher"].queryset = (
                user.journalist_publications.all().order_by("name")
            )
        self.fields["publisher"].empty_label = "Independent article"
        self.apply_site_widgets()


class NewsletterForm(SiteFormMixin, forms.ModelForm):
    """Create or edit a newsletter from the website."""

    class Meta:
        """Define the fields available on the newsletter form."""
        model = Newsletter
        fields = ["title", "description", "author", "articles"]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Describe this collection..."}
            ),
            "articles": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, user, **kwargs):
        """Configure author and article choices for the current user."""
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["articles"].queryset = Article.objects.filter(
            approved=True
        ).order_by("-created_at")
        self.fields["author"].queryset = User.objects.filter(
            role=User.JOURNALIST
        ).order_by("username")
        if (
            user.is_journalist
            and not user.is_editor
        ):
            self.fields.pop("author")
        else:
            self.fields["author"].label = "Journalist author"
        self.apply_site_widgets()

    def save(self, commit=True):
        """Persist the newsletter and default the author when needed."""
        instance = super().save(commit=False)
        if not self.cleaned_data.get("author"):
            instance.author = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance
