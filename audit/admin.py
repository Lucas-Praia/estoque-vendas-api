from django.contrib import admin

from core.admin import ReadOnlyAdminMixin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['dt_created_at', 'tx_action', 'tx_model', 'tx_object_id', 'tx_object_repr', 'tx_username', 'tx_ip']
    list_filter = ['tx_action', 'tx_model', 'dt_created_at']
    search_fields = ['tx_username', 'tx_object_repr', 'tx_object_id', 'tx_request_id']
