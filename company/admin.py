from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['tx_name', 'tx_cnpj', 'tx_phone']

    def has_add_permission(self, request):
        return not Company.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
