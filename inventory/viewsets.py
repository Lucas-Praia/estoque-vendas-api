from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsManager

from . import services
from .filters import StockEntryFilter, StockMovementFilter
from .models import StockEntry, StockMovement
from .serializers import (
    NewStockEntrySerializer,
    StockAdjustmentSerializer,
    StockEntrySerializer,
    StockMovementSerializer,
)


class StockEntryViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Entradas são histórico: podem ser criadas e consultadas, mas não editadas."""

    queryset = StockEntry.objects.select_related('id_supplier', 'id_user').prefetch_related('items__id_product')
    serializer_class = StockEntrySerializer
    permission_classes = [IsManager]
    filterset_class = StockEntryFilter
    ordering_fields = '__all__'
    ordering = '-id_stock_entry'

    @extend_schema(request=NewStockEntrySerializer, responses=StockEntrySerializer)
    def create(self, request):
        data = NewStockEntrySerializer(data=request.data)
        data.is_valid(raise_exception=True)

        entry = services.register_stock_entry(user=request.user, **data.validated_data)

        entry = self.get_queryset().get(pk=entry.pk)
        return Response(StockEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related('id_product', 'id_user')
    serializer_class = StockMovementSerializer
    permission_classes = [IsManager]
    filterset_class = StockMovementFilter
    ordering_fields = '__all__'
    ordering = '-id_stock_movement'

    @extend_schema(request=StockAdjustmentSerializer, responses=StockMovementSerializer)
    @action(detail=False, methods=['post'])
    def adjust(self, request):
        """Corrige o estoque de um produto para a quantidade contada."""
        data = StockAdjustmentSerializer(data=request.data)
        data.is_valid(raise_exception=True)

        movement = services.adjust_stock(user=request.user, **data.validated_data)
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)
