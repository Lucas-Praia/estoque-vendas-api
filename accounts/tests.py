from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient

from core.tests.factories import (
    create_admin,
    create_manager,
    create_operator,
    create_product,
    create_supplier,
    create_user,
)
from audit.models import AuditLog
from sales.models import PaymentMethod
from sales.services import register_sale

from .roles import Role, get_role


class JwtLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        create_operator(username='caixa1')

    def test_login_returns_tokens_and_token_accesses_api(self):
        response = self.client.post('/api/auth/token/', {'username': 'caixa1', 'password': 'senha-teste'})
        self.assertEqual(response.status_code, 200)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        me = self.client.get('/api/auth/me/')

        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['username'], 'caixa1')
        self.assertEqual(me.data['tx_role'], Role.OPERATOR)
        self.assertEqual(me.data['tx_role_name'], 'Operador')

    def test_wrong_password_is_rejected(self):
        response = self.client.post('/api/auth/token/', {'username': 'caixa1', 'password': 'errada'})
        self.assertEqual(response.status_code, 401)

    def test_api_requires_login(self):
        self.assertEqual(self.client.get('/api/product/').status_code, 401)

    def test_passwords_are_hashed_with_argon2(self):
        user = get_user_model().objects.get(username='caixa1')
        self.assertTrue(user.password.startswith('argon2'))

class RoleResolutionTests(TestCase):
    def test_highest_group_wins_and_superuser_is_admin(self):
        user = create_operator()
        user.groups.add(*create_manager(username='outro').groups.all())
        self.assertEqual(get_role(user), Role.MANAGER)

        superuser = get_user_model().objects.create_superuser('root', password='senha-teste')
        self.assertEqual(get_role(superuser), Role.ADMIN)

    def test_user_without_group_has_no_role(self):
        self.assertIsNone(get_role(create_user()))


class RolePermissionTests(TestCase):
    """Matriz de acesso: o que cada perfil pode fazer na API."""

    def setUp(self):
        self.client = APIClient()
        self.product = create_product(nb_stock=Decimal('10'))

    def as_user(self, user):
        self.client.force_authenticate(user)
        return self.client

    def test_user_without_role_is_blocked_but_sees_own_profile(self):
        client = self.as_user(create_user(username='sem_perfil'))
        self.assertEqual(client.get('/api/product/').status_code, 403)
        self.assertEqual(client.get('/api/auth/me/').data['tx_role'], None)

    def test_operator_reads_registry_but_cannot_change_it(self):
        client = self.as_user(create_operator())
        self.assertEqual(client.get('/api/product/').status_code, 200)
        self.assertEqual(client.patch(f'/api/product/{self.product.pk}/', {'nb_price': '1.00'}, format='json').status_code, 403)
        self.assertEqual(client.post('/api/category/', {'tx_name': 'Bebidas'}, format='json').status_code, 403)

    def test_manager_changes_registry(self):
        client = self.as_user(create_manager())
        response = client.patch(f'/api/product/{self.product.pk}/', {'nb_price': '1.00'}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_only_manager_handles_stock(self):
        self.assertEqual(self.as_user(create_operator()).get('/api/stock_movement/').status_code, 403)
        self.assertEqual(self.as_user(create_manager()).get('/api/stock_movement/').status_code, 200)

        response = self.as_user(create_manager(username='gerente2')).post('/api/stock_entry/', {
            'id_supplier': create_supplier().pk,
            'items': [{'id_product': self.product.pk, 'nb_quantity': '1', 'nb_unit_cost': '2.00'}],
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_operator_sells_and_sees_only_own_sales(self):
        operator = create_operator()
        other = create_operator(username='caixa2')
        client = self.as_user(operator)

        response = client.post('/api/sale/', {
            'items': [{'id_product': self.product.pk, 'nb_quantity': '1'}],
            'payments': [{'tx_method': PaymentMethod.PIX, 'nb_amount': '25.00'}],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self._sell_as(other)

        ids = [sale['id_sale'] for sale in client.get('/api/sale/').data['results']]
        self.assertEqual(ids, [response.data['id_sale']])

    def test_only_manager_cancels_sale(self):
        sale = self._sell_as(create_operator())

        self.assertEqual(self.as_user(create_operator(username='caixa2')).post(f'/api/sale/{sale.pk}/cancel/').status_code, 403)
        self.assertEqual(self.as_user(create_manager()).post(f'/api/sale/{sale.pk}/cancel/').status_code, 200)

    def test_only_admin_edits_company_and_reads_audit(self):
        manager = self.as_user(create_manager())
        self.assertEqual(manager.patch('/api/company/', {'tx_name': 'X'}, format='json').status_code, 403)
        self.assertEqual(manager.get('/api/audit_log/').status_code, 403)

        admin = self.as_user(create_admin())
        self.assertEqual(admin.patch('/api/company/', {'tx_name': 'X'}, format='json').status_code, 200)
        self.assertEqual(admin.get('/api/audit_log/').status_code, 200)

    def _sell_as(self, user):
        return register_sale(
            user=user,
            items=[{'id_product': self.product, 'nb_quantity': Decimal('1')}],
            payments=[{'tx_method': PaymentMethod.PIX, 'nb_amount': Decimal('25.00')}],
        )


class EmployeeAdminTests(TestCase):
    """O dono do negócio (perfil Administrador) cadastra os funcionários pelo admin do Django."""

    def setUp(self):
        self.owner = create_admin(username='dono')
        self.owner.refresh_from_db()
        self.client.force_login(self.owner)

    def test_admin_role_gets_admin_access_and_loses_it_when_removed(self):
        self.assertTrue(self.owner.is_staff)

        self.owner.groups.set([])
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_staff)

    def test_other_roles_do_not_enter_admin(self):
        manager = create_manager()
        manager.refresh_from_db()
        self.assertFalse(manager.is_staff)

    def test_owner_creates_employee_with_a_role(self):
        manager_group = Group.objects.get(name=Role.MANAGER.label)
        response = self.client.post('/admin/auth/user/add/', {
            'username': 'joao',
            'password1': 'Senha-Forte-2026',
            'password2': 'Senha-Forte-2026',
            'groups': [manager_group.pk],
        })

        self.assertEqual(response.status_code, 302)
        employee = get_user_model().objects.get(username='joao')
        self.assertEqual(get_role(employee), Role.MANAGER)
        self.assertTrue(AuditLog.objects.filter(
            tx_model='auth.User', tx_object_id=str(employee.pk), js_changes__groups__added=[Role.MANAGER.label],
        ).exists())

    def test_owner_cannot_see_superusers_or_grant_superuser(self):
        root = get_user_model().objects.create_superuser('dev', password='senha-teste')

        self.assertEqual(self.client.get(f'/admin/auth/user/{root.pk}/change/').status_code, 302)
        page = self.client.get(f'/admin/auth/user/{create_operator().pk}/change/').content.decode()
        self.assertNotIn('name="is_superuser"', page)
        self.assertNotIn('name="user_permissions"', page)

    def test_only_role_groups_are_offered(self):
        Group.objects.create(name='Grupo qualquer')
        page = self.client.get('/admin/auth/user/add/').content.decode()
        self.assertIn('Gerente', page)
        self.assertNotIn('Grupo qualquer', page)

    def test_admin_group_has_admin_permissions_after_migrate(self):
        codenames = set(Group.objects.get(name=Role.ADMIN.label).permissions.values_list('codename', flat=True))
        self.assertTrue({'add_user', 'change_user', 'change_company', 'view_auditlog'} <= codenames)
        self.assertNotIn('delete_user', codenames)
