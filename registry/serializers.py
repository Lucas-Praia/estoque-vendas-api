from rest_framework import serializers

from core.serializers import BaseModelSerializer

from .models import Category, Customer, Product, Supplier


class CategorySerializer(BaseModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(BaseModelSerializer):
    tx_category_name = serializers.CharField(source='id_category.tx_name', read_only=True)
    bl_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['nb_stock']


class SupplierSerializer(BaseModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class CustomerSerializer(BaseModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
