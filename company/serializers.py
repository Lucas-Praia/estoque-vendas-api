from core.serializers import BaseModelSerializer

from .models import Company


class CompanySerializer(BaseModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ['id_company']
