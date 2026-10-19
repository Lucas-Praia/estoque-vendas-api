from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from registry.models import UnitOfMeasure
from core.exceptions import BusinessRuleError
from core.tests.factories import create_product, create_user

from .models import PaymentMethod, SaleStatus
from .services import cancel_sale, register_sale


class RegisterSaleTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.product = create_product(nb_price='25.00', nb_stock=Decimal('10'))

    def sell(self, nb_quantity='2', payments=None, **kwargs):
        return register_sale(
            user=self.user,
            items=[{'id_product': self.product, 'nb_quantity': Decimal(nb_quantity)}],
            payments=payments or [{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('50.00')}],
            **kwargs,
        )

    def test_lowers_stock_and_calculates_total(self):
        sale = self.sell(nb_discount=Decimal('5.00'), payments=[
            {'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('45.00')},
        ])

        self.product.refresh_from_db()
        self.assertEqual(self.product.nb_stock, Decimal('8'))
        self.assertEqual(sale.nb_subtotal, Decimal('50.00'))
        self.assertEqual(sale.nb_total, Decimal('45.00'))

    def test_calculates_change_in_cash(self):
        sale = self.sell(payments=[{'tx_method': PaymentMethod.CASH, 'nb_amount': Decimal('100.00')}])

        self.assertEqual(sale.payments.get().nb_change, Decimal('50.00'))

    def test_rejects_change_outside_cash(self):
        with self.assertRaises(BusinessRuleError):
            self.sell(payments=[{'tx_method': PaymentMethod.CREDIT, 'nb_amount': Decimal('60.00')}])

    def test_rejects_insufficient_payment(self):
        with self.assertRaises(BusinessRuleError):
            self.sell(payments=[{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('10.00')}])

    def test_rejects_insufficient_stock_without_saving(self):
        with self.assertRaises(BusinessRuleError):
            self.sell(nb_quantity='11', payments=[{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('275.00')}])

        self.product.refresh_from_db()
        self.assertEqual(self.product.nb_stock, Decimal('10'))
        self.assertFalse(self.product.sale_items.exists())

    def test_rejects_fractional_quantity_for_unit_product(self):
        with self.assertRaises(BusinessRuleError):
            self.sell(nb_quantity='1.5')

    def test_accepts_fractional_quantity_for_kilogram_product(self):
        self.product.tx_unit = UnitOfMeasure.KILOGRAM
        self.product.save()

        sale = self.sell(nb_quantity='0.350', payments=[{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('8.75')}])

        self.assertEqual(sale.nb_total, Decimal('8.75'))

    def test_same_product_in_two_lines_is_lowered_in_sequence(self):
        register_sale(
            user=self.user,
            items=[
                {'id_product': self.product, 'nb_quantity': Decimal('3')},
                {'id_product': self.product, 'nb_quantity': Decimal('4')},
            ],
            payments=[{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('175.00')}],
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.nb_stock, Decimal('3'))
        resulting = list(self.product.stock_movements.order_by('id_stock_movement').values_list('nb_resulting_stock', flat=True))
        self.assertEqual(resulting, [Decimal('7'), Decimal('3')])

    def test_sale_query_count_does_not_grow_with_items(self):
        products = [create_product(f'Produto {i}', nb_stock=Decimal('10')) for i in range(20)]

        def sell(count):
            register_sale(
                user=self.user,
                items=[{'id_product': p, 'nb_quantity': Decimal('1')} for p in products[:count]],
                payments=[{'tx_method': PaymentMethod.CASH, 'nb_amount': Decimal('1000')}],
            )

        with CaptureQueriesContext(connection) as small:
            sell(2)
        with CaptureQueriesContext(connection) as large:
            sell(20)
        self.assertEqual(len(small.captured_queries), len(large.captured_queries))


class CancelSaleTests(TestCase):
    def test_returns_stock_and_cannot_cancel_twice(self):
        user = create_user()
        product = create_product(nb_price='10.00', nb_stock=Decimal('5'))
        sale = register_sale(
            user=user,
            items=[{'id_product': product, 'nb_quantity': Decimal('3')}],
            payments=[{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('30.00')}],
        )

        cancel_sale(sale=sale, user=user)

        product.refresh_from_db()
        sale.refresh_from_db()
        self.assertEqual(product.nb_stock, Decimal('5'))
        self.assertEqual(sale.tx_status, SaleStatus.CANCELED)
        with self.assertRaises(BusinessRuleError):
            cancel_sale(sale=sale, user=user)
