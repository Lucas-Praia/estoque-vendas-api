from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save

from . import recorder
from .models import AuditAction

# Tabelas auditadas. Itens de venda/entrada e pagamentos entram junto com o registro principal;
# a movimentação de estoque já é, ela própria, um histórico.
AUDITED_MODELS = [
    'auth.User',
    'company.Company',
    'registry.Category',
    'registry.Product',
    'registry.Supplier',
    'registry.Customer',
    'inventory.StockEntry',
    'sales.Sale',
]


def connect():
    for label in AUDITED_MODELS:
        model = apps.get_model(label)
        pre_save.connect(_remember_previous, sender=model, dispatch_uid=f'audit_pre_save_{label}')
        post_save.connect(_record_save, sender=model, dispatch_uid=f'audit_post_save_{label}')
        post_delete.connect(_record_delete, sender=model, dispatch_uid=f'audit_post_delete_{label}')

    m2m_changed.connect(_record_groups_change, sender=get_user_model().groups.through, dispatch_uid='audit_user_groups')
    user_logged_in.connect(_record_login, dispatch_uid='audit_user_logged_in')
    user_login_failed.connect(_record_login_failed, dispatch_uid='audit_user_login_failed')


def _remember_previous(sender, instance, **kwargs):
    previous = None
    if not instance._state.adding:
        previous = sender._default_manager.filter(pk=instance.pk).first()
    instance._audit_before = recorder.snapshot(previous) if previous else None


def _record_save(sender, instance, created, **kwargs):
    after = recorder.snapshot(instance)
    before = getattr(instance, '_audit_before', None)

    if created or before is None:
        recorder.record(AuditAction.CREATE, instance=instance, changes=recorder.masked(after))
        return

    changes = recorder.diff(before, after)
    if changes:
        recorder.record(AuditAction.UPDATE, instance=instance, changes=changes)


def _record_delete(sender, instance, **kwargs):
    recorder.record(AuditAction.DELETE, instance=instance, changes=recorder.masked(recorder.snapshot(instance)))


def _record_groups_change(sender, instance, action, reverse, pk_set, **kwargs):
    """Quem deu ou tirou qual perfil de quem: mudança de grupo não passa pelo post_save."""
    if reverse or action not in {'post_add', 'post_remove'} or not pk_set:
        return
    names = sorted(Group.objects.filter(pk__in=pk_set).values_list('name', flat=True))
    key = 'added' if action == 'post_add' else 'removed'
    recorder.record(AuditAction.UPDATE, instance=instance, changes={'groups': {key: names}})


def _record_login(sender, request, user, **kwargs):
    recorder.record_login(user)


def _record_login_failed(sender, credentials, request=None, **kwargs):
    recorder.record_login_failed(credentials.get('username'))
