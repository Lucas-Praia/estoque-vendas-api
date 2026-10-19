from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from accounts.permissions import IsAdmin

from .models import Company
from .serializers import CompanySerializer


class CompanyView(generics.RetrieveUpdateAPIView):
    """Marca do negócio. Leitura pública (o front mostra a logo já na tela de login); edição só por administrador."""

    serializer_class = CompanySerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsAdmin()]

    def get_object(self):
        return Company.load()
