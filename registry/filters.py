import django_filters

from .models import Category, Customer, Product, Supplier


class CategoryFilter(django_filters.FilterSet):
    tx_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Category
        fields = ['tx_name', 'bl_active']


class ProductFilter(django_filters.FilterSet):
    tx_description = django_filters.CharFilter(lookup_expr='icontains')
    tx_barcode = django_filters.CharFilter(lookup_expr='exact')
    nb_price_min = django_filters.NumberFilter(field_name='nb_price', lookup_expr='gte')
    nb_price_max = django_filters.NumberFilter(field_name='nb_price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['tx_description', 'tx_barcode', 'id_category', 'tx_unit', 'bl_active']


class SupplierFilter(django_filters.FilterSet):
    tx_corporate_name = django_filters.CharFilter(lookup_expr='icontains')
    tx_trade_name = django_filters.CharFilter(lookup_expr='icontains')
    tx_cnpj = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Supplier
        fields = ['tx_corporate_name', 'tx_trade_name', 'tx_cnpj', 'bl_active']


class CustomerFilter(django_filters.FilterSet):
    tx_name = django_filters.CharFilter(lookup_expr='icontains')
    tx_cpf_cnpj = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Customer
        fields = ['tx_name', 'tx_cpf_cnpj', 'bl_active']
