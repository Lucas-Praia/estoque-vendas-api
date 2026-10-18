import django_filters

from .models import StockEntry, StockMovement


class StockEntryFilter(django_filters.FilterSet):
    tx_invoice_number = django_filters.CharFilter(lookup_expr='icontains')
    id_supplier__tx_corporate_name = django_filters.CharFilter(lookup_expr='icontains')
    dt_entry_start = django_filters.DateFilter(field_name='dt_entry', lookup_expr='gte')
    dt_entry_end = django_filters.DateFilter(field_name='dt_entry', lookup_expr='lte')

    class Meta:
        model = StockEntry
        fields = ['tx_invoice_number', 'id_supplier', 'id_supplier__tx_corporate_name']


class StockMovementFilter(django_filters.FilterSet):
    id_product__tx_description = django_filters.CharFilter(lookup_expr='icontains')
    dt_created_at_start = django_filters.DateFilter(field_name='dt_created_at', lookup_expr='date__gte')
    dt_created_at_end = django_filters.DateFilter(field_name='dt_created_at', lookup_expr='date__lte')

    class Meta:
        model = StockMovement
        fields = ['id_product', 'id_product__tx_description', 'tx_type']
