from django.test import TestCase
from rest_framework.test import APIClient

from core.tests.factories import create_admin, create_manager

from .models import Company


class CompanyTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_anyone_can_read_branding(self):
        response = self.client.get('/api/company/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tx_name'], 'MINHA EMPRESA')

    def test_only_admin_can_edit(self):
        self.client.force_authenticate(create_manager())
        response = self.client.patch('/api/company/', {'tx_name': 'Mercadinho Bom Preço'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_admin_edits_and_there_is_only_one_company(self):
        self.client.force_authenticate(create_admin())

        response = self.client.patch('/api/company/', {'tx_name': 'Mercadinho Bom Preço'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tx_name'], 'MERCADINHO BOM PREÇO')
        self.assertEqual(Company.objects.count(), 1)
