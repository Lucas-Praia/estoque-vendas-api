"""Monta e grava os registros de auditoria."""

from django.db.models.fields.files import FieldFile

from . import context
from .models import AuditAction, AuditLog

SENSITIVE_FIELDS = {'password'}
MASK = '***'
# Campos que mudam sozinhos ou já têm histórico próprio (nb_stock → StockMovement).
IGNORED_FIELDS = {'dt_created_at', 'dt_modified_at', 'last_login', 'nb_stock'}


def snapshot(instance):
    """Valores atuais do registro (senhas incluídas, só para comparar; nunca são gravadas)."""
    return {field.attname: _value(instance, field) for field in instance._meta.concrete_fields}


def masked(values):
    return {field: MASK if field in SENSITIVE_FIELDS else value for field, value in values.items()}


def diff(before, after):
    return {
        field: [MASK, MASK] if field in SENSITIVE_FIELDS else [before.get(field), value]
        for field, value in after.items()
        if field not in IGNORED_FIELDS and before.get(field) != value
    }


def record(action, *, instance=None, changes=None, user=None, username=''):
    user = user or context.get_user()
    AuditLog.objects.create(
        id_user=user,
        tx_username=user.get_username() if user else username,
        tx_action=action,
        tx_model=instance._meta.label if instance is not None else '',
        tx_object_id=str(instance.pk) if instance is not None else '',
        tx_object_repr=str(instance)[:255] if instance is not None else '',
        js_changes=changes or {},
        tx_request_id=context.get_request_id(),
        **context.get_client_info(),
    )


def record_login(user):
    record(AuditAction.LOGIN, user=user)


def record_login_failed(username):
    record(AuditAction.LOGIN_FAILED, username=username or '')


def _value(instance, field):
    value = field.value_from_object(instance)
    if isinstance(value, FieldFile):
        return value.name or None
    return value
