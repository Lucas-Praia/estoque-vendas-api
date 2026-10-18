from rest_framework import serializers


class BaseModelSerializer(serializers.ModelSerializer):
    """Converte os textos para maiúsculo antes de validar, para a checagem de duplicidade funcionar."""

    def to_internal_value(self, data):
        fields = self.Meta.model.uppercase_fields()
        data = {
            key: value.upper() if key in fields and isinstance(value, str) else value
            for key, value in data.items()
        }
        return super().to_internal_value(data)
