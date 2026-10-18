from rest_framework import generics

from .serializers import MeSerializer


class MeView(generics.RetrieveAPIView):
    """Dados do usuário logado (o front usa para mostrar o operador e liberar telas de administrador)."""

    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user
