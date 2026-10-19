"""Acesso do dono do negócio (perfil Administrador) ao admin do Django.

As permissões ficam aqui, no código, para serem iguais em toda instalação: ninguém
precisa marcar a lista de permissões do grupo à mão em cada cliente.
"""

from django.contrib.auth.models import Group, Permission

from .roles import Role

ADMIN_GROUP_PERMISSIONS = {
    'auth': ['add_user', 'change_user', 'view_user', 'view_group'],
    'company': ['change_company', 'view_company'],
    'registry': [
        f'{action}_{model}'
        for model in ('category', 'product', 'supplier', 'customer')
        for action in ('add', 'change', 'delete', 'view')
    ],
    'inventory': ['view_stockentry', 'view_stockmovement'],
    'sales': ['view_sale'],
    'audit': ['view_auditlog'],
}


def sync_admin_group_permissions():
    """Idempotente: roda após cada migrate e ignora permissões que ainda não existem."""
    group = Group.objects.filter(name=Role.ADMIN.label).first()
    if group is None:
        return
    permissions = Permission.objects.none()
    for app_label, codenames in ADMIN_GROUP_PERMISSIONS.items():
        permissions |= Permission.objects.filter(content_type__app_label=app_label, codename__in=codenames)
    group.permissions.set(permissions)
    group.user_set.filter(is_staff=False).update(is_staff=True)


def sync_staff_flag(user):
    """Só quem tem perfil Administrador (ou é superusuário) entra no admin do Django."""
    if hasattr(user, '_cached_role'):
        del user._cached_role
    group_names = set(user.groups.values_list('name', flat=True))
    is_staff = user.is_superuser or Role.ADMIN.label in group_names
    if user.is_staff != is_staff:
        user.is_staff = is_staff
        user.save(update_fields=['is_staff'])
