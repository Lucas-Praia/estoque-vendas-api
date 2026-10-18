from django.contrib import admin


class ReadOnlyAdminMixin:
    """Para registros que só podem ser criados pelos services (ex.: vendas, entradas)."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyInline(ReadOnlyAdminMixin, admin.TabularInline):
    extra = 0
