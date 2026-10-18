from decimal import Decimal

from django.test import TestCase

from core.exceptions import BusinessRuleError
from core.tests.factories import create_product, create_supplier, create_user

from .models import MovementType
from .services import adjust_stock, register_stock_entry


class RegisterStockEntryTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.supplier = create_supplier()
        self.product = create_product()

    def test_adds_to_stock_and_updates_cost(self):
        register_stock_entry(
            user=self.user, id_supplier=self.supplier,
            items=[{'id_product': self.product, 'nb_quantity': Decimal('10'), 'nb_unit_cost': Decimal('18.50')}],
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.nb_stock, Decimal('10'))
        self.assertEqual(self.product.nb_cost_price, Decimal('18.50'))
        self.assertEqual(self.product.stock_movements.get().tx_type, MovementType.IN)

    def test_requires_items(self):
        with self.assertRaises(BusinessRuleError):
            register_stock_entry(user=self.user, id_supplier=self.supplier, items=[])


class AdjustStockTests(TestCase):
    def test_sets_stock_to_counted_quantity(self):
        user = create_user()
        product = create_product(nb_stock=Decimal('10'))

        movement = adjust_stock(
            user=user, id_product=product, nb_counted_stock=Decimal('7'), tx_reason='Inventário'
        )

        product.refresh_from_db()
        self.assertEqual(product.nb_stock, Decimal('7'))
        self.assertEqual(movement.nb_quantity, Decimal('-3'))
