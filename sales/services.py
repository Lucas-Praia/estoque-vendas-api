from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from registry.models import UnitOfMeasure
from core.exceptions import BusinessRuleError
from inventory.models import MovementType
from inventory.services import move_stock_batch

from .models import Payment, PaymentMethod, Sale, SaleItem, SaleStatus

FRACTIONAL_UNITS = {UnitOfMeasure.KILOGRAM, UnitOfMeasure.LITER}


@transaction.atomic
def register_sale(*, user, items, payments, nb_discount=Decimal('0'), id_customer=None):
    """Registra a venda, dá baixa no estoque e calcula o troco.

    items: lista de dicts com 'id_product' e 'nb_quantity'.
    payments: lista de dicts com 'tx_method' e 'nb_amount' (valor recebido do cliente).
    """
    if not items:
        raise BusinessRuleError('A venda precisa de pelo menos um item.')
    if not payments:
        raise BusinessRuleError('Informe pelo menos uma forma de pagamento.')

    for item in items:
        _validate_item(item['id_product'], item['nb_quantity'])

    nb_subtotal = sum((item['nb_quantity'] * item['id_product'].nb_price for item in items), Decimal('0'))
    nb_subtotal = nb_subtotal.quantize(Decimal('0.01'))
    if nb_discount > nb_subtotal:
        raise BusinessRuleError('O desconto não pode ser maior que o subtotal.')
    nb_total = nb_subtotal - nb_discount

    nb_change = _calculate_change(nb_total, payments)

    sale = Sale.objects.create(
        id_user=user,
        id_customer=id_customer,
        nb_subtotal=nb_subtotal,
        nb_discount=nb_discount,
        nb_total=nb_total,
    )

    SaleItem.objects.bulk_create(
        SaleItem(
            id_sale=sale,
            id_product=item['id_product'],
            nb_quantity=item['nb_quantity'],
            nb_unit_price=item['id_product'].nb_price,
        )
        for item in items
    )
    move_stock_batch(
        lines=[(item['id_product'], -item['nb_quantity']) for item in items],
        tx_type=MovementType.OUT,
        user=user,
        tx_reason=f'Venda #{sale.pk}',
    )
    Payment.objects.bulk_create(_build_payments(sale, payments, nb_change))

    return sale


@transaction.atomic
def cancel_sale(*, sale, user):
    """Cancela a venda e devolve os produtos ao estoque."""
    sale = Sale.objects.select_for_update().get(pk=sale.pk)
    if sale.tx_status == SaleStatus.CANCELED:
        raise BusinessRuleError(f'A venda #{sale.pk} já está cancelada.')

    move_stock_batch(
        lines=[(item.id_product, item.nb_quantity) for item in sale.items.select_related('id_product')],
        tx_type=MovementType.IN,
        user=user,
        tx_reason=f'Cancelamento da venda #{sale.pk}',
    )

    sale.tx_status = SaleStatus.CANCELED
    sale.dt_canceled_at = timezone.now()
    sale.save(update_fields=['tx_status', 'dt_canceled_at', 'dt_modified_at'])
    return sale


def _build_payments(sale, payments, nb_change):
    """O troco fica registrado no primeiro pagamento em dinheiro."""
    built = []
    for payment in payments:
        payment_change = nb_change if payment['tx_method'] == PaymentMethod.CASH else Decimal('0')
        built.append(Payment(
            id_sale=sale,
            tx_method=payment['tx_method'],
            nb_amount=payment['nb_amount'],
            nb_change=payment_change,
        ))
        if payment_change:
            nb_change = Decimal('0')
    return built


def _validate_item(product, nb_quantity):
    if not product.bl_active:
        raise BusinessRuleError(f'O produto {product.tx_description} está inativo.')
    if product.tx_unit not in FRACTIONAL_UNITS and nb_quantity != nb_quantity.to_integral_value():
        raise BusinessRuleError(
            f'O produto {product.tx_description} é vendido por {product.get_tx_unit_display().lower()}; '
            'a quantidade deve ser inteira.'
        )


def _calculate_change(nb_total, payments):
    nb_paid = sum((payment['nb_amount'] for payment in payments), Decimal('0'))
    if nb_paid < nb_total:
        raise BusinessRuleError(f'Pagamento insuficiente. Faltam R$ {nb_total - nb_paid}.')

    nb_change = nb_paid - nb_total
    nb_paid_in_cash = sum(
        (p['nb_amount'] for p in payments if p['tx_method'] == PaymentMethod.CASH), Decimal('0')
    )
    if nb_change > nb_paid_in_cash:
        raise BusinessRuleError('O valor pago passa do total. Troco só é possível em dinheiro.')
    return nb_change
