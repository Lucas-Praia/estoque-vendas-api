from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class BusinessRuleError(Exception):
    """Erro de regra de negócio (ex.: estoque insuficiente). Vira resposta 400 na API."""


def exception_handler(exc, context):
    if isinstance(exc, BusinessRuleError):
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, ProtectedError):
        return Response(
            {'detail': 'Não é possível excluir: existem registros vinculados. Desative-o em vez de excluir.'},
            status=status.HTTP_409_CONFLICT,
        )

    return drf_exception_handler(exc, context)
