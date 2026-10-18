from decimal import Decimal

from rest_framework import serializers

from registry.models import Product, Supplier

from .models import StockEntry, StockEntryItem, StockMovement


class StockEntryItemSerializer(serializers.ModelSerializer):
    tx_product_description = serializers.CharField(source='id_product.tx_description', read_only=True)
    nb_subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = StockEntryItem
        fields = '__all__'


class StockEntrySerializer(serializers.ModelSerializer):
    tx_supplier_name = serializers.CharField(source='id_supplier.__str__', read_only=True)
    tx_user_name = serializers.CharField(source='id_user.username', read_only=True)
    items = StockEntryItemSerializer(many=True, read_only=True)
    nb_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = StockEntry
        fields = '__all__'


class NewStockEntryItemSerializer(serializers.Serializer):
    id_product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    nb_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0.001'))
    nb_unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))


class NewStockEntrySerializer(serializers.Serializer):
    id_supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.filter(bl_active=True))
    tx_invoice_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    dt_entry = serializers.DateField(required=False)
    tx_note = serializers.CharField(required=False, allow_blank=True)
    items = NewStockEntryItemSerializer(many=True, allow_empty=False)


class StockMovementSerializer(serializers.ModelSerializer):
    tx_product_description = serializers.CharField(source='id_product.tx_description', read_only=True)
    tx_user_name = serializers.CharField(source='id_user.username', read_only=True)

    class Meta:
        model = StockMovement
        fields = '__all__'


class StockAdjustmentSerializer(serializers.Serializer):
    id_product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    nb_counted_stock = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0'))
    tx_reason = serializers.CharField(max_length=255)
