from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsManager
from accounts.roles import Role, has_role

from . import services
from .filters import SaleFilter
from .models import Sale
from .serializers import NewSaleSerializer, SaleSerializer


class SaleViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):

    queryset = Sale.objects.select_related('id_user', 'id_customer').prefetch_related(
        'items__id_product', 'payments'
    )
    serializer_class = SaleSerializer
    filterset_class = SaleFilter
    ordering_fields = '__all__'
    ordering = '-id_sale'

    def get_queryset(self):
        queryset = super().get_queryset()
        if has_role(self.request.user, Role.MANAGER):
            return queryset
        return queryset.filter(id_user=self.request.user)

    @extend_schema(request=NewSaleSerializer, responses=SaleSerializer)
    def create(self, request):
        data = NewSaleSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        sale = services.register_sale(user=request.user, **data.validated_data)

        return Response(self._serialize(sale), status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=SaleSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsManager])
    def cancel(self, request, pk=None):
        sale = services.cancel_sale(sale=self.get_object(), user=request.user)
        return Response(self._serialize(sale))

    def _serialize(self, sale):
        return SaleSerializer(self.get_queryset().get(pk=sale.pk)).data
