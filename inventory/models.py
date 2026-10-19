from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from registry.models import Product, Supplier
from core.models import BaseModel


class StockEntry(BaseModel):
    """Compra/recebimento de mercadoria de um fornecedor."""

    id_stock_entry = models.BigAutoField(
        primary_key=True,
        db_column='id_stock_entry'
    )
    id_supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='stock_entries',
        verbose_name='fornecedor',
        db_column='id_supplier'
    )
    id_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stock_entries',
        verbose_name='usuário',
        db_column='id_user'
    )
    tx_invoice_number = models.CharField(
        'número da nota',
        max_length=50,
        blank=True,
        db_column='tx_invoice_number'
    )
    dt_entry = models.DateField(
        'data de entrada',
        default=timezone.localdate,
        db_column='dt_entry'
    )
    tx_note = models.TextField(
        'observação',
        blank=True,
        db_column='tx_note'
    )

    class Meta:
        ordering = ['-dt_entry', '-id_stock_entry']
        verbose_name = 'entrada de mercadoria'
        verbose_name_plural = 'entradas de mercadoria'

    def __str__(self):
        return f'Entrada #{self.pk} - {self.id_supplier}'

    @property
    def nb_total(self):
        return sum((item.nb_subtotal for item in self.items.all()), Decimal('0'))


class StockEntryItem(models.Model):
    id_stock_entry_item = models.BigAutoField(
        primary_key=True,
        db_column='id_stock_entry_item'
    )
    id_stock_entry = models.ForeignKey(
        StockEntry,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='entrada',
        db_column='id_stock_entry'
    )
    id_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='stock_entry_items',
        verbose_name='produto',
        db_column='id_product'
    )
    nb_quantity = models.DecimalField(
        'quantidade',
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        db_column='nb_quantity'
    )
    nb_unit_cost = models.DecimalField(
        'custo unitário',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        db_column='nb_unit_cost'
    )

    class Meta:
        verbose_name = 'item da entrada'
        verbose_name_plural = 'itens da entrada'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nb_quantity__gt=0),
                name='stock_entry_item_nb_quantity_positive',
            ),
        ]

    def __str__(self):
        return f'{self.nb_quantity} x {self.id_product}'

    @property
    def nb_subtotal(self):
        return self.nb_quantity * self.nb_unit_cost


class MovementType(models.TextChoices):
    IN = 'IN', 'Entrada'
    OUT = 'OUT', 'Saída'
    ADJUSTMENT = 'ADJUSTMENT', 'Ajuste'


class StockMovement(BaseModel):
    """Histórico de tudo que alterou o estoque de um produto."""

    id_stock_movement = models.BigAutoField(
        primary_key=True,
        db_column='id_stock_movement'
    )
    id_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name='produto',
        db_column='id_product'
    )
    id_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name='usuário',
        db_column='id_user'
    )
    tx_type = models.CharField(
        'tipo',
        max_length=10,
        choices=MovementType.choices,
        db_column='tx_type'
    )
    nb_quantity = models.DecimalField(
        'quantidade',
        max_digits=12,
        decimal_places=3,
        help_text='Positiva soma ao estoque, negativa subtrai.',
        db_column='nb_quantity'
    )
    nb_resulting_stock = models.DecimalField(
        'estoque resultante',
        max_digits=12,
        decimal_places=3,
        db_column='nb_resulting_stock'
    )
    tx_reason = models.CharField(
        'motivo',
        max_length=255,
        blank=True,
        db_column='tx_reason'
    )

    class Meta:
        ordering = ['-dt_created_at']
        verbose_name = 'movimentação de estoque'
        indexes = [models.Index(fields=['dt_created_at'], name='stock_movement_dt_created_idx')]
        verbose_name_plural = 'movimentações de estoque'

    def __str__(self):
        return f'{self.get_tx_type_display()} {self.nb_quantity} - {self.id_product}'
