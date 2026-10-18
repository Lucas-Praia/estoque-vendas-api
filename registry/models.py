from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel

NON_NEGATIVE = [MinValueValidator(Decimal('0'))]


class UnitOfMeasure(models.TextChoices):
    UNIT = 'UN', 'Unidade'
    KILOGRAM = 'KG', 'Quilo'
    LITER = 'L', 'Litro'
    BOX = 'CX', 'Caixa'
    BUNDLE = 'FD', 'Fardo'
    PACK = 'PCT', 'Pacote'


class Category(BaseModel):
    id_category = models.BigAutoField(
        primary_key=True,
        db_column='id_category'
    )
    tx_name = models.CharField(
        'nome',
        max_length=100,
        unique=True,
        db_column='tx_name'
    )
    bl_active = models.BooleanField(
        'ativo',
        default=True,
        db_column='bl_active'
    )

    class Meta:
        ordering = ['tx_name']
        verbose_name = 'categoria'

    def __str__(self):
        return self.tx_name


class Product(BaseModel):
    id_product = models.BigAutoField(
        primary_key=True,
        db_column='id_product'
    )
    tx_description = models.CharField(
        'descrição',
        max_length=150,
        db_column='tx_description'
    )
    tx_barcode = models.CharField(
        'código de barras',
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_column='tx_barcode'
    )
    id_category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='categoria',
        db_column='id_category'
    )
    tx_unit = models.CharField(
        'unidade de medida',
        max_length=3,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.UNIT,
        db_column='tx_unit'
    )
    nb_cost_price = models.DecimalField(
        'preço de custo',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        validators=NON_NEGATIVE,
        db_column='nb_cost_price'
    )
    nb_price = models.DecimalField(
        'preço de venda',
        max_digits=10,
        decimal_places=2,
        validators=NON_NEGATIVE,
        db_column='nb_price'
    )
    nb_stock = models.DecimalField(
        'estoque atual',
        max_digits=12,
        decimal_places=3,
        default=Decimal('0'),
        editable=False,
        db_column='nb_stock'
    )
    nb_min_stock = models.DecimalField(
        'estoque mínimo',
        max_digits=12,
        decimal_places=3,
        default=Decimal('0'),
        validators=NON_NEGATIVE,
        db_column='nb_min_stock'
    )
    bl_active = models.BooleanField(
        'ativo',
        default=True,
        db_column='bl_active'
    )

    class Meta:
        ordering = ['tx_description']
        verbose_name = 'produto'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nb_price__gte=0),
                name='product_nb_price_non_negative',
            ),
        ]

    def __str__(self):
        return self.tx_description

    @property
    def bl_low_stock(self):
        return self.nb_stock <= self.nb_min_stock


class Supplier(BaseModel):
    id_supplier = models.BigAutoField(
        primary_key=True,
        db_column='id_supplier'
    )
    tx_corporate_name = models.CharField(
        'razão social',
        max_length=150,
        db_column='tx_corporate_name'
    )
    tx_trade_name = models.CharField(
        'nome fantasia',
        max_length=150,
        blank=True,
        db_column='tx_trade_name'
    )
    tx_cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        unique=True,
        db_column='tx_cnpj'
    )
    tx_phone = models.CharField(
        'telefone',
        max_length=20,
        blank=True,
        db_column='tx_phone'
    )
    tx_email = models.EmailField(
        'e-mail',
        max_length=128,
        blank=True,
        db_column='tx_email'
    )
    bl_active = models.BooleanField(
        'ativo',
        default=True,
        db_column='bl_active'
    )

    class Meta:
        ordering = ['tx_corporate_name']
        verbose_name = 'fornecedor'
        verbose_name_plural = 'fornecedores'

    def __str__(self):
        return self.tx_trade_name or self.tx_corporate_name


class Customer(BaseModel):
    id_customer = models.BigAutoField(
        primary_key=True,
        db_column='id_customer'
    )
    tx_name = models.CharField(
        'nome',
        max_length=128,
        db_column='tx_name'
    )
    tx_cpf_cnpj = models.CharField(
        'CPF/CNPJ',
        max_length=18,
        unique=True,
        null=True,
        blank=True,
        db_column='tx_cpf_cnpj'
    )
    tx_phone = models.CharField(
        'telefone',
        max_length=20,
        blank=True,
        db_column='tx_phone'
    )
    tx_email = models.EmailField(
        'e-mail',
        max_length=128,
        blank=True,
        db_column='tx_email'
    )
    tx_address = models.CharField(
        'endereço',
        max_length=255,
        blank=True,
        db_column='tx_address'
    )
    bl_active = models.BooleanField(
        'ativo',
        default=True,
        db_column='bl_active'
    )

    class Meta:
        ordering = ['tx_name']
        verbose_name = 'cliente'

    def __str__(self):
        return self.tx_name
