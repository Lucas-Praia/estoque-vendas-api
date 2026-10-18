import django_filters

from .models import Sale


class SaleFilter(django_filters.FilterSet):
    id_customer__tx_name = django_filters.CharFilter(lookup_expr='icontains')
    dt_created_at_start = django_filters.DateFilter(field_name='dt_created_at', lookup_expr='date__gte')
    dt_created_at_end = django_filters.DateFilter(field_name='dt_created_at', lookup_expr='date__lte')

    class Meta:
        model = Sale
        fields = ['tx_status', 'id_user', 'id_customer', 'id_customer__tx_name']
