from decimal import Decimal

from rest_framework import serializers

from registry.models import Customer, Product

from .models import Payment, PaymentMethod, Sale, SaleItem


class SaleItemSerializer(serializers.ModelSerializer):
    tx_product_description = serializers.CharField(source='id_product.tx_description', read_only=True)
    nb_subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = SaleItem
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class SaleSerializer(serializers.ModelSerializer):
    tx_user_name = serializers.CharField(source='id_user.username', read_only=True)
    tx_customer_name = serializers.CharField(source='id_customer.tx_name', read_only=True, default=None)
    items = SaleItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'


class NewSaleItemSerializer(serializers.Serializer):
    id_product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    nb_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0.001'))


class NewPaymentSerializer(serializers.Serializer):
    tx_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    nb_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))


class NewSaleSerializer(serializers.Serializer):
    id_customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.filter(bl_active=True), required=False, allow_null=True
    )
    nb_discount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('0'), required=False, default=Decimal('0')
    )
    items = NewSaleItemSerializer(many=True, allow_empty=False)
    payments = NewPaymentSerializer(many=True, allow_empty=False)
