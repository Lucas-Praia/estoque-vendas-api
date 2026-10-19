from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from registry.models import Product
from core.exceptions import BusinessRuleError

from .models import MovementType, StockEntry, StockEntryItem, StockMovement


@transaction.atomic
def move_stock_batch(*, lines, tx_type, user, tx_reason=''):
    """Única porta de alteração do estoque: atualiza os saldos e grava o histórico.

    lines: lista de (product, nb_quantity); quantidade positiva soma, negativa subtrai.
    Trava todos os produtos de uma vez, sempre em ordem de id, para duas vendas
    simultâneas nunca esperarem uma pela outra em ordem cruzada (deadlock).
    """
    product_ids = sorted({product.pk for product, _ in lines})
    locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=product_ids).order_by('pk')}

    now = timezone.now()
    movements = []
    for product, nb_quantity in lines:
        current = locked[product.pk]
        new_stock = current.nb_stock + nb_quantity
        if new_stock < 0:
            raise BusinessRuleError(
                f'Estoque insuficiente para {current.tx_description}. Disponível: {current.nb_stock}.'
            )
        current.nb_stock = new_stock
        current.dt_modified_at = now
        movement = StockMovement(
            id_product=current,
            id_user=user,
            tx_type=tx_type,
            nb_quantity=nb_quantity,
            nb_resulting_stock=new_stock,
            tx_reason=tx_reason,
        )
        movement._uppercase_texts()
        movements.append(movement)

    Product.objects.bulk_update(locked.values(), ['nb_stock', 'dt_modified_at'])
    return StockMovement.objects.bulk_create(movements)


def move_stock(*, product, nb_quantity, tx_type, user, tx_reason=''):
    return move_stock_batch(lines=[(product, nb_quantity)], tx_type=tx_type, user=user, tx_reason=tx_reason)[0]


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

    StockEntryItem.objects.bulk_create(
        StockEntryItem(
            id_stock_entry=entry,
            id_product=item['id_product'],
            nb_quantity=item['nb_quantity'],
            nb_unit_cost=item['nb_unit_cost'],
        )
        for item in items
    )
    move_stock_batch(
        lines=[(item['id_product'], item['nb_quantity']) for item in items],
        tx_type=MovementType.IN,
        user=user,
        tx_reason=f'Entrada #{entry.pk}',
    )
    _update_cost_prices(items)

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


def _update_cost_prices(items):
    """Grava o último custo pago. Usa save() (e não update em lote) para a mudança de preço ficar na auditoria;
    só salva quando o custo de fato mudou, que é a minoria dos itens de uma nota."""
    last_cost = {item['id_product'].pk: (item['id_product'], item['nb_unit_cost']) for item in items}
    for product, nb_unit_cost in last_cost.values():
        if product.nb_cost_price != nb_unit_cost:
            product.nb_cost_price = nb_unit_cost
            product.save(update_fields=['nb_cost_price', 'dt_modified_at'])
