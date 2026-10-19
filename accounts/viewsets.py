from rest_framework import generics, permissions

from .serializers import MeSerializer


class MeView(generics.RetrieveAPIView):
    """Dados do usuário logado e o perfil dele (o front usa para liberar as telas).

    Não exige perfil: quem ainda não tem um precisa conseguir ver isso para pedir acesso.
    """

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
