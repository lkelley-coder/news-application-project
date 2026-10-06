"""Website views for creating and managing publishers."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PublisherForm
from .models import Publisher


def can_manage_publisher(user, publisher):
    """Return True if the user is an editor affiliated with the publisher.

    Superusers may manage every publisher.
    """
    if user.is_superuser:
        return True
    return (
        user.is_editor
        and publisher.editors.filter(pk=user.pk).exists()
    )


@login_required
def publisher_list(request):
    """List publishers; editors also see the management actions."""
    publishers = Publisher.objects.prefetch_related(
        "editors", "journalists"
    ).order_by("name")
    managed_ids = {
        publisher.pk
        for publisher in publishers
        if can_manage_publisher(request.user, publisher)
    }
    return render(
        request,
        "publishers/list.html",
        {"publishers": publishers, "managed_ids": managed_ids},
    )


@login_required
def publisher_create_page(request):
    """Let an editor create a publisher and join as an editor."""
    if not request.user.is_editor:
        raise Http404
    form = PublisherForm(
        request.POST if request.method == "POST" else None,
        initial={"editors": [request.user.pk]},
    )
    if request.method == "POST" and form.is_valid():
        publisher = form.save()
        if request.user.is_editor and request.user.role == request.user.EDITOR:
            publisher.editors.add(request.user)
        messages.success(request, "Publisher created.")
        return redirect("publisher-list")
    return render(
        request,
        "articles/form.html",
        {
            "form": form,
            "page_title": "Create a publisher",
            "submit_label": "Create publisher",
            "cancel_url": "publisher-list",
        },
    )


@login_required
def publisher_edit_page(request, pk):
    """Edit a publisher and its affiliated editors and journalists."""
    publisher = get_object_or_404(Publisher, pk=pk)
    if not can_manage_publisher(request.user, publisher):
        raise Http404
    form = PublisherForm(request.POST or None, instance=publisher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Publisher changes saved.")
        return redirect("publisher-list")
    return render(
        request,
        "articles/form.html",
        {
            "form": form,
            "page_title": f"Manage {publisher.name}",
            "submit_label": "Save changes",
            "cancel_url": "publisher-list",
        },
    )


@login_required
@require_POST
def publisher_delete_page(request, pk):
    """Delete a publisher unless articles still reference it."""
    publisher = get_object_or_404(Publisher, pk=pk)
    if not can_manage_publisher(request.user, publisher):
        raise Http404
    try:
        publisher.delete()
    except ProtectedError:
        messages.error(
            request,
            "This publisher still has articles and cannot be deleted.",
        )
    else:
        messages.success(request, "Publisher deleted.")
    return redirect("publisher-list")
