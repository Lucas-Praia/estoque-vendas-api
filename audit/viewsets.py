from rest_framework import viewsets

from accounts.permissions import IsAdmin

from .filters import AuditLogFilter
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Consulta da auditoria, só para administradores. Não existe rota para alterar ou apagar."""

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filterset_class = AuditLogFilter
    ordering_fields = '__all__'
    ordering = '-id_audit_log'
