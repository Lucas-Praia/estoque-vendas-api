from django.contrib import admin

from .models import Category, Customer, Product, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['tx_name', 'bl_active']
    list_filter = ['bl_active']
    search_fields = ['tx_name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['tx_description', 'tx_barcode', 'id_category', 'tx_unit', 'nb_price', 'nb_stock', 'bl_active']
    list_filter = ['id_category', 'tx_unit', 'bl_active']
    search_fields = ['tx_description', 'tx_barcode']
    readonly_fields = ['nb_stock']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['tx_corporate_name', 'tx_trade_name', 'tx_cnpj', 'tx_phone', 'bl_active']
    list_filter = ['bl_active']
    search_fields = ['tx_corporate_name', 'tx_trade_name', 'tx_cnpj']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['tx_name', 'tx_cpf_cnpj', 'tx_phone', 'bl_active']
    list_filter = ['bl_active']
    search_fields = ['tx_name', 'tx_cpf_cnpj']
