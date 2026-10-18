from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = 'CREATE', 'Criação'
    UPDATE = 'UPDATE', 'Alteração'
    DELETE = 'DELETE', 'Exclusão'
    LOGIN = 'LOGIN', 'Login'
    LOGIN_FAILED = 'LOGIN_FAILED', 'Login recusado'


class AuditLog(models.Model):
    """Registro imutável de quem fez o quê. Não herda BaseModel: o conteúdo é gravado exatamente como aconteceu."""

    id_audit_log = models.BigAutoField(
        primary_key=True,
        db_column='id_audit_log'
    )
    id_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='usuário',
        db_column='id_user'
    )
    tx_username = models.CharField(
        'usuário (no momento)',
        max_length=150,
        blank=True,
        db_column='tx_username'
    )
    tx_action = models.CharField(
        'ação',
        max_length=12,
        choices=AuditAction.choices,
        db_column='tx_action'
    )
    tx_model = models.CharField(
        'tabela',
        max_length=100,
        blank=True,
        db_column='tx_model'
    )
    tx_object_id = models.CharField(
        'id do registro',
        max_length=64,
        blank=True,
        db_column='tx_object_id'
    )
    tx_object_repr = models.CharField(
        'registro',
        max_length=255,
        blank=True,
        db_column='tx_object_repr'
    )
    js_changes = models.JSONField(
        'alterações',
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text='Criação/exclusão: valores do registro. Alteração: {campo: [antes, depois]}.',
        db_column='js_changes'
    )
    tx_ip = models.GenericIPAddressField(
        'IP',
        null=True,
        blank=True,
        db_column='tx_ip'
    )
    tx_user_agent = models.CharField(
        'navegador',
        max_length=255,
        blank=True,
        db_column='tx_user_agent'
    )
    tx_request_id = models.CharField(
        'ID da requisição',
        max_length=64,
        blank=True,
        db_index=True,
        db_column='tx_request_id'
    )
    dt_created_at = models.DateTimeField(
        'data',
        auto_now_add=True,
        db_index=True,
        db_column='dt_created_at'
    )

    class Meta:
        ordering = ['-dt_created_at']
        verbose_name = 'log de auditoria'
        verbose_name_plural = 'logs de auditoria'
        indexes = [models.Index(fields=['tx_model', 'tx_object_id'], name='audit_model_object_idx')]

    def __str__(self):
        return f'{self.get_tx_action_display()} {self.tx_model} #{self.tx_object_id} por {self.tx_username or "sistema"}'
