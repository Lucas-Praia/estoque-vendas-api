from django.contrib import admin

from core.admin import ReadOnlyAdminMixin, ReadOnlyInline

from .models import StockEntry, StockEntryItem, StockMovement


class StockEntryItemInline(ReadOnlyInline):
    model = StockEntryItem


@admin.register(StockEntry)
class StockEntryAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['id_stock_entry', 'id_supplier', 'tx_invoice_number', 'dt_entry', 'id_user']
    list_filter = ['dt_entry', 'id_supplier']
    search_fields = ['tx_invoice_number', 'id_supplier__tx_corporate_name']
    inlines = [StockEntryItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['dt_created_at', 'id_product', 'tx_type', 'nb_quantity', 'nb_resulting_stock', 'id_user']
    list_filter = ['tx_type', 'dt_created_at']
    search_fields = ['id_product__tx_description', 'id_product__tx_barcode']
