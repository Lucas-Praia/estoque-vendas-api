from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .roles import HIERARCHY, Role

User = get_user_model()

ROLE_GROUP_NAMES = [role.label for role in Role]

EMPLOYEE_FIELDSETS = (
    (None, {'fields': ('username', 'password')}),
    ('Dados pessoais', {'fields': ('first_name', 'last_name', 'email')}),
    ('Acesso', {'fields': ('is_active', 'groups')}),
    ('Datas', {'fields': ('last_login', 'date_joined')}),
)

EMPLOYEE_ADD_FIELDSETS = (
    (None, {'classes': ('wide',), 'fields': ('username', 'password1', 'password2', 'groups')}),
)


admin.site.unregister(User)


@admin.register(User)
class EmployeeAdmin(UserAdmin):
    """Cadastro de funcionários pelo dono do negócio.

    Para quem não é superusuário: não vê nem edita superusuários, não concede superusuário
    nem permissões avulsas, só escolhe entre os grupos de perfil e não exclui (desativa).
    """

    list_display = ['username', 'first_name', 'last_name', 'role_name', 'is_active', 'last_login']
    list_filter = ['is_active', 'groups']

    @admin.display(description='perfil')
    def role_name(self, user):
        names = set(user.groups.values_list('name', flat=True))
        if user.is_superuser:
            return Role.ADMIN.label
        return next((role.label for role in reversed(HIERARCHY) if role.label in names), '—')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset if request.user.is_superuser else queryset.filter(is_superuser=False)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        return EMPLOYEE_ADD_FIELDSETS if obj is None else EMPLOYEE_FIELDSETS

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_readonly_fields(request, obj)
        return ['last_login', 'date_joined']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'groups':
            kwargs['queryset'] = Group.objects.filter(name__in=ROLE_GROUP_NAMES)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
