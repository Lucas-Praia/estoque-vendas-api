from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_migrate

from .admin_access import sync_admin_group_permissions, sync_staff_flag


def connect():
    user_model = get_user_model()
    post_migrate.connect(_on_post_migrate, dispatch_uid='accounts_sync_admin_permissions')
    m2m_changed.connect(_on_groups_changed, sender=user_model.groups.through, dispatch_uid='accounts_sync_staff')


def _on_post_migrate(sender, **kwargs):
    sync_admin_group_permissions()


def _on_groups_changed(sender, instance, action, reverse, **kwargs):
    if reverse or action not in {'post_add', 'post_remove', 'post_clear'}:
        return
    sync_staff_flag(instance)
