from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.viewsets import MeView
from audit.viewsets import AuditLogViewSet
from company.viewsets import CompanyView
from registry import viewsets as registry_viewsets
from inventory import viewsets as inventory_viewsets
from sales import viewsets as sales_viewsets

router = DefaultRouter()
router.register(r'category', registry_viewsets.CategoryViewSet)
router.register(r'product', registry_viewsets.ProductViewSet)
router.register(r'supplier', registry_viewsets.SupplierViewSet)
router.register(r'customer', registry_viewsets.CustomerViewSet)
router.register(r'stock_entry', inventory_viewsets.StockEntryViewSet)
router.register(r'stock_movement', inventory_viewsets.StockMovementViewSet)
router.register(r'sale', sales_viewsets.SaleViewSet)
router.register(r'audit_log', AuditLogViewSet)


urlpatterns = [
    path('', lambda request: redirect('api/docs/', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', MeView.as_view(), name='me'),
    path('api/company/', CompanyView.as_view(), name='company'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
