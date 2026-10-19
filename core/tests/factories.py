from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from accounts.roles import Role
from registry.models import Category, Product, Supplier, UnitOfMeasure


def create_user(username='operador', role=None):
    user = get_user_model().objects.create_user(username=username, password='senha-teste')
    if role:
        user.groups.add(Group.objects.get(name=role.label))
    return user


def create_operator(username='operador'):
    return create_user(username, Role.OPERATOR)


def create_manager(username='gerente'):
    return create_user(username, Role.MANAGER)


def create_admin(username='admin'):
    return create_user(username, Role.ADMIN)


def create_product(tx_description='Arroz 5kg', nb_price='25.00', tx_unit=UnitOfMeasure.UNIT, **kwargs):
    category, _ = Category.objects.get_or_create(tx_name='MERCEARIA')
    return Product.objects.create(
        tx_description=tx_description, id_category=category, nb_price=Decimal(nb_price),
        tx_unit=tx_unit, **kwargs,
    )


def create_supplier(tx_cnpj='00.000.000/0001-00'):
    return Supplier.objects.create(tx_corporate_name='Fornecedor Teste', tx_cnpj=tx_cnpj)
