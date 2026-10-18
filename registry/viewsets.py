from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import CategoryFilter, CustomerFilter, ProductFilter, SupplierFilter
from .models import Category, Customer, Product, Supplier
from .serializers import CategorySerializer, CustomerSerializer, ProductSerializer, SupplierSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_class = CategoryFilter
    ordering_fields = '__all__'
    ordering = 'tx_name'


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('id_category')
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    ordering_fields = '__all__'
    ordering = 'tx_description'

    @action(detail=False, url_path=r'barcode/(?P<tx_barcode>[^/]+)')
    def barcode(self, request, tx_barcode):
        """Busca o produto pelo código de barras (usado ao bipar na venda)."""
        product = get_object_or_404(self.get_queryset(), tx_barcode=tx_barcode, bl_active=True)
        return Response(self.get_serializer(product).data)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_class = SupplierFilter
    ordering_fields = '__all__'
    ordering = 'tx_corporate_name'


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_class = CustomerFilter
    ordering_fields = '__all__'
    ordering = 'tx_name'
