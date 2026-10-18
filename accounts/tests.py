from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.tests.factories import create_user


class JwtLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        create_user(username='caixa1')

    def test_login_returns_tokens_and_token_accesses_api(self):
        response = self.client.post('/api/auth/token/', {'username': 'caixa1', 'password': 'senha-teste'})
        self.assertEqual(response.status_code, 200)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        me = self.client.get('/api/auth/me/')

        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data['username'], 'caixa1')

    def test_wrong_password_is_rejected(self):
        response = self.client.post('/api/auth/token/', {'username': 'caixa1', 'password': 'errada'})
        self.assertEqual(response.status_code, 401)

    def test_api_requires_login(self):
        self.assertEqual(self.client.get('/api/product/').status_code, 401)

    def test_passwords_are_hashed_with_argon2(self):
        user = get_user_model().objects.get(username='caixa1')
        self.assertTrue(user.password.startswith('argon2'))
