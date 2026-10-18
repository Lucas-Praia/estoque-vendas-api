import django_filters

from .models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    tx_username = django_filters.CharFilter(lookup_expr='icontains')
    tx_model = django_filters.CharFilter(lookup_expr='iexact')
    dt_created_at_start = django_filters.DateFilter(field_name='dt_created_at', lookup_expr='date__gte')
    dt_created_at_end = django_filters.DateFilter(field_name='dt_created_at', lookup_expr='date__lte')

    class Meta:
        model = AuditLog
        fields = ['tx_action', 'tx_model', 'tx_object_id', 'id_user', 'tx_username', 'tx_request_id']
