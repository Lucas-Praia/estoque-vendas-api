from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from registry.models import Customer, Product
from core.models import BaseModel

NON_NEGATIVE = [MinValueValidator(Decimal('0'))]


class SaleStatus(models.TextChoices):
    COMPLETED = 'COMPLETED', 'Finalizada'
    CANCELED = 'CANCELED', 'Cancelada'


class PaymentMethod(models.TextChoices):
    CASH = 'CASH', 'Dinheiro'
    PIX = 'PIX', 'Pix'
    DEBIT = 'DEBIT', 'Cartão de débito'
    CREDIT = 'CREDIT', 'Cartão de crédito'


class Sale(BaseModel):
    id_sale = models.BigAutoField(
        primary_key=True,
        db_column='id_sale'
    )
    id_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='operador',
        db_column='id_user'
    )
    id_customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='sales',
        null=True,
        blank=True,
        verbose_name='cliente',
        db_column='id_customer'
    )
    tx_status = models.CharField(
        'status',
        max_length=10,
        choices=SaleStatus.choices,
        default=SaleStatus.COMPLETED,
        db_column='tx_status'
    )
    nb_subtotal = models.DecimalField(
        'subtotal',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=NON_NEGATIVE,
        db_column='nb_subtotal'
    )
    nb_discount = models.DecimalField(
        'desconto',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=NON_NEGATIVE,
        db_column='nb_discount'
    )
    nb_total = models.DecimalField(
        'total',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=NON_NEGATIVE,
        db_column='nb_total'
    )
    dt_canceled_at = models.DateTimeField(
        'cancelada em',
        null=True,
        blank=True,
        db_column='dt_canceled_at'
    )

    class Meta:
        ordering = ['-dt_created_at']
        verbose_name = 'venda'
        indexes = [models.Index(fields=['dt_created_at'], name='sale_dt_created_at_idx')]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nb_discount__lte=models.F('nb_subtotal')),
                name='sale_nb_discount_up_to_subtotal',
            ),
        ]

    def __str__(self):
        return f'Venda #{self.pk}'


class SaleItem(models.Model):
    id_sale_item = models.BigAutoField(
        primary_key=True,
        db_column='id_sale_item'
    )
    id_sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='venda',
        db_column='id_sale'
    )
    id_product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items',
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
    nb_unit_price = models.DecimalField(
        'preço unitário',
        max_digits=10,
        decimal_places=2,
        validators=NON_NEGATIVE,
        help_text='Preço no momento da venda; não muda se o produto mudar de preço.',
        db_column='nb_unit_price'
    )

    class Meta:
        verbose_name = 'item da venda'
        verbose_name_plural = 'itens da venda'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nb_quantity__gt=0),
                name='sale_item_nb_quantity_positive',
            ),
        ]

    def __str__(self):
        return f'{self.nb_quantity} x {self.id_product}'

    @property
    def nb_subtotal(self):
        return self.nb_quantity * self.nb_unit_price


class Payment(models.Model):
    id_payment = models.BigAutoField(
        primary_key=True,
        db_column='id_payment'
    )
    id_sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='venda',
        db_column='id_sale'
    )
    tx_method = models.CharField(
        'forma de pagamento',
        max_length=8,
        choices=PaymentMethod.choices,
        db_column='tx_method'
    )
    nb_amount = models.DecimalField(
        'valor',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        db_column='nb_amount'
    )
    nb_change = models.DecimalField(
        'troco',
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        validators=NON_NEGATIVE,
        db_column='nb_change'
    )

    class Meta:
        verbose_name = 'pagamento'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nb_amount__gt=0),
                name='payment_nb_amount_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(nb_change=0) | models.Q(tx_method=PaymentMethod.CASH),
                name='payment_nb_change_cash_only',
            ),
        ]

    def __str__(self):
        return f'{self.get_tx_method_display()} R$ {self.nb_amount}'
