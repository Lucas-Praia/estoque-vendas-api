from django.contrib import admin

from core.admin import ReadOnlyAdminMixin, ReadOnlyInline

from .models import Payment, Sale, SaleItem


class SaleItemInline(ReadOnlyInline):
    model = SaleItem


class PaymentInline(ReadOnlyInline):
    model = Payment


@admin.register(Sale)
class SaleAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['id_sale', 'dt_created_at', 'id_user', 'id_customer', 'tx_status', 'nb_total']
    list_filter = ['tx_status', 'dt_created_at', 'id_user']
    search_fields = ['id_sale', 'id_customer__tx_name']
    inlines = [SaleItemInline, PaymentInline]
