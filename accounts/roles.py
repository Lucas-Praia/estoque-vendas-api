from django.db import models


class Role(models.TextChoices):

    OPERATOR = 'OPERATOR', 'Operador'
    MANAGER = 'MANAGER', 'Gerente'
    ADMIN = 'ADMIN', 'Administrador'

HIERARCHY = [Role.OPERATOR, Role.MANAGER, Role.ADMIN]


def get_role(user):
    if user is None or not user.is_authenticated:
        return None
    if not hasattr(user, '_cached_role'):
        user._cached_role = _resolve_role(user)
    return user._cached_role


def has_role(user, minimum):
    role = get_role(user)
    return role is not None and HIERARCHY.index(role) >= HIERARCHY.index(minimum)


def _resolve_role(user):
    if user.is_superuser:
        return Role.ADMIN
    group_names = set(user.groups.values_list('name', flat=True))
    roles = [role for role in HIERARCHY if role.label in group_names]
    return roles[-1] if roles else None
