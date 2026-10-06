"""Signal handlers that keep user roles and groups in sync."""
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_migrate, post_save
from django.dispatch import receiver

from .models import User

ROLE_GROUPS = {
    User.READER: "Reader",
    User.EDITOR: "Editor",
    User.JOURNALIST: "Journalist",
}


@receiver(post_save, sender=User)
def sync_user_role_group(sender, instance, **kwargs):
    """Keep a user's role-based group membership aligned after saves."""
    # Keep the persisted role and role-based group membership synchronized.
    role_group_names = list(ROLE_GROUPS.values())
    group, _ = Group.objects.get_or_create(name=ROLE_GROUPS[instance.role])
    instance.groups.remove(
        *instance.groups.filter(name__in=role_group_names).exclude(pk=group.pk)
    )
    instance.groups.add(group)

    if instance.role != User.READER:
        # Only readers should retain reader subscription selections.
        instance.publisher_subscriptions.clear()
        instance.journalist_subscriptions.clear()


@receiver(m2m_changed, sender=User.groups.through)
def sync_user_role_from_group(sender, instance, action, pk_set, **kwargs):
    """Update a user's stored role when a role group is assigned."""
    # Mirror role-group assignments back onto the stored role field.
    if action != "post_add" or not pk_set:
        return

    role_group_names = set(ROLE_GROUPS.values())
    assigned_roles = list(
        Group.objects.filter(pk__in=pk_set, name__in=role_group_names)
        .values_list("name", flat=True)
    )
    if not assigned_roles:
        return

    role = next(
        role
        for role, group_name in ROLE_GROUPS.items()
        if group_name == assigned_roles[0]
    )
    if instance.role != role:
        instance.role = role
        instance.save(update_fields=["role"])


@receiver(post_migrate)
def configure_role_groups(sender, **kwargs):
    """Create role groups and assign article permissions after migrations."""
    # Rebuild the role groups after migrations so article and newsletter
    # permissions always match the current policy.
    role_content_types = {
        "app_label": "articles",
        "model__in": ("article", "newsletter"),
    }
    for role, group_name in ROLE_GROUPS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = Permission.objects.filter(
            content_type__app_label=role_content_types["app_label"],
            content_type__model__in=role_content_types["model__in"],
        )
        if role == User.READER:
            permissions = permissions.filter(codename__startswith="view_")
        elif role == User.EDITOR:
            permissions = permissions.filter(
                Q(codename__startswith="view_")
                | Q(codename__startswith="change_")
                | Q(codename__startswith="delete_")
                | Q(codename="add_newsletter")
            )
        group.permissions.set(permissions)
