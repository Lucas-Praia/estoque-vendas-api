from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .roles import Role, get_role


class LoginSerializer(TokenObtainPairSerializer):
    """Login por JWT que avisa o Django do login (auditoria e last_login), como o login do admin já faz."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user_logged_in.send(sender=self.user.__class__, request=self.context.get('request'), user=self.user)
        return data


class MeSerializer(serializers.ModelSerializer):
    tx_full_name = serializers.CharField(source='get_full_name', read_only=True)
    tx_role = serializers.SerializerMethodField()
    tx_role_name = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'tx_full_name', 'email', 'is_staff', 'tx_role', 'tx_role_name']
        read_only_fields = fields

    @extend_schema_field(serializers.ChoiceField(choices=Role.choices, allow_null=True))
    def get_tx_role(self, user):
        return get_role(user)

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_tx_role_name(self, user):
        role = get_role(user)
        return role.label if role else None
