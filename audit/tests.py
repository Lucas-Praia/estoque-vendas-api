from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from core.tests.factories import create_admin, create_manager, create_operator, create_product, create_supplier, create_user
from inventory.services import register_stock_entry

from .models import AuditAction, AuditLog


class AuditTrailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_manager()
        self.client.force_authenticate(self.user)

    def test_create_via_api_records_user_and_request_id(self):
        category = create_product().id_category
        response = self.client.post('/api/product/', {
            'tx_description': 'Feijão 1kg', 'id_category': category.pk, 'nb_price': '8.90',
        }, format='json', HTTP_X_REQUEST_ID='abc-123')

        log = AuditLog.objects.get(tx_action=AuditAction.CREATE, tx_object_id=str(response.data['id_product']))
        self.assertEqual(log.tx_model, 'registry.Product')
        self.assertEqual(log.id_user, self.user)
        self.assertEqual(log.tx_request_id, 'abc-123')
        self.assertEqual(log.js_changes['tx_description'], 'FEIJÃO 1KG')

    def test_update_records_only_changed_fields(self):
        product = create_product(nb_price='10.00')

        self.client.patch(f'/api/product/{product.pk}/', {'nb_price': '12.50'}, format='json')

        log = AuditLog.objects.get(tx_action=AuditAction.UPDATE, tx_object_id=str(product.pk))
        self.assertEqual(log.js_changes, {'nb_price': ['10.00', '12.50']})

    def test_stock_changes_are_left_to_stock_movement(self):
        product = create_product()
        AuditLog.objects.all().delete()

        register_stock_entry(
            user=self.user, id_supplier=create_supplier(),
            items=[{'id_product': product, 'nb_quantity': Decimal('5'), 'nb_unit_cost': Decimal('3.00')}],
        )

        product_logs = AuditLog.objects.filter(tx_model='registry.Product', tx_action=AuditAction.UPDATE)
        self.assertEqual(product_logs.get().js_changes, {'nb_cost_price': ['0.00', '3.00']})

    def test_delete_is_recorded(self):
        product = create_product()

        self.client.delete(f'/api/product/{product.pk}/')

        self.assertTrue(AuditLog.objects.filter(tx_action=AuditAction.DELETE, tx_object_id=str(product.pk)).exists())

    def test_password_is_never_stored(self):
        self.user.set_password('nova-senha-segura')
        self.user.save()

        log = AuditLog.objects.filter(tx_model='auth.User', tx_action=AuditAction.UPDATE).latest('dt_created_at')
        self.assertEqual(log.js_changes['password'], ['***', '***'])
        self.assertNotIn('nova-senha-segura', str(AuditLog.objects.values_list('js_changes', flat=True)))


class LoginAuditTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        create_user(username='caixa1')

    def test_successful_and_failed_logins_are_recorded(self):
        self.client.post('/api/auth/token/', {'username': 'caixa1', 'password': 'senha-teste'})
        self.client.post('/api/auth/token/', {'username': 'caixa1', 'password': 'errada'})

        self.assertTrue(AuditLog.objects.filter(tx_action=AuditAction.LOGIN, tx_username='caixa1').exists())
        self.assertTrue(AuditLog.objects.filter(tx_action=AuditAction.LOGIN_FAILED, tx_username='caixa1').exists())


class AuditAccessTests(TestCase):
    def test_only_admin_reads_audit_log(self):
        client = APIClient()
        client.force_authenticate(create_operator())
        self.assertEqual(client.get('/api/audit_log/').status_code, 403)

        client.force_authenticate(create_admin())
        self.assertEqual(client.get('/api/audit_log/').status_code, 200)


class RequestIdTests(TestCase):
    def test_every_response_has_request_id(self):
        response = APIClient().get('/api/company/')
        self.assertRegex(response['X-Request-ID'], r'^[a-f0-9]{32}$')

    def test_reuses_safe_request_id_from_client(self):
        response = APIClient().get('/api/company/', HTTP_X_REQUEST_ID='front-42')
        self.assertEqual(response['X-Request-ID'], 'front-42')

    def test_ignores_unsafe_request_id(self):
        response = APIClient().get('/api/company/', HTTP_X_REQUEST_ID='x\nfalso log')
        self.assertNotEqual(response['X-Request-ID'], 'x\nfalso log')
