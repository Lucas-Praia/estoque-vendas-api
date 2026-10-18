from decimal import Decimal

from django.db import transaction

from registry.models import Product
from core.exceptions import BusinessRuleError

from .models import MovementType, StockEntry, StockEntryItem, StockMovement


@transaction.atomic
def move_stock(*, product, nb_quantity, tx_type, user, tx_reason=''):
    """Única porta de alteração do estoque: atualiza o saldo e grava o histórico."""
    product = Product.objects.select_for_update().get(pk=product.pk)
    new_stock = product.nb_stock + nb_quantity

    if new_stock < 0:
        raise BusinessRuleError(
            f'Estoque insuficiente para {product.tx_description}. Disponível: {product.nb_stock}.'
        )

    product.nb_stock = new_stock
    product.save(update_fields=['nb_stock', 'dt_modified_at'])

    return StockMovement.objects.create(
        id_product=product,
        id_user=user,
        tx_type=tx_type,
        nb_quantity=nb_quantity,
        nb_resulting_stock=new_stock,
        tx_reason=tx_reason,
    )


@transaction.atomic
def register_stock_entry(*, user, id_supplier, items, tx_invoice_number='', dt_entry=None, tx_note=''):
    """Registra a nota do fornecedor, soma ao estoque e atualiza o preço de custo dos produtos.

    items: lista de dicts com 'id_product', 'nb_quantity' e 'nb_unit_cost'.
    """
    if not items:
        raise BusinessRuleError('A entrada precisa de pelo menos um item.')

    entry = StockEntry(id_supplier=id_supplier, id_user=user, tx_invoice_number=tx_invoice_number, tx_note=tx_note)
    if dt_entry:
        entry.dt_entry = dt_entry
    entry.save()

    for item in items:
        product = item['id_product']
        StockEntryItem.objects.create(
            id_stock_entry=entry,
            id_product=product,
            nb_quantity=item['nb_quantity'],
            nb_unit_cost=item['nb_unit_cost'],
        )
        move_stock(
            product=product,
            nb_quantity=item['nb_quantity'],
            tx_type=MovementType.IN,
            user=user,
            tx_reason=f'Entrada #{entry.pk}',
        )
        product.nb_cost_price = item['nb_unit_cost']
        product.save(update_fields=['nb_cost_price', 'dt_modified_at'])

    return entry


@transaction.atomic
def adjust_stock(*, user, id_product, nb_counted_stock, tx_reason):
    """Corrige o estoque para o valor contado (inventário, perda, quebra...)."""
    product = Product.objects.select_for_update().get(pk=id_product.pk)
    difference = Decimal(nb_counted_stock) - product.nb_stock
    if difference == 0:
        raise BusinessRuleError('O estoque contado é igual ao estoque atual.')

    return move_stock(
        product=product,
        nb_quantity=difference,
        tx_type=MovementType.ADJUSTMENT,
        user=user,
        tx_reason=tx_reason,
    )
