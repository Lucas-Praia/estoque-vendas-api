from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class LoginSerializer(TokenObtainPairSerializer):
    """Login por JWT que avisa o Django do login (auditoria e last_login), como o login do admin já faz."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user_logged_in.send(sender=self.user.__class__, request=self.context.get('request'), user=self.user)
        return data


class MeSerializer(serializers.ModelSerializer):
    tx_full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'tx_full_name', 'email', 'is_staff']
        read_only_fields = fields
