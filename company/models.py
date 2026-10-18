from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models

from core.models import BaseModel

SINGLETON_ID = 1
MAX_LOGO_SIZE_MB = 2


def validate_logo_size(file):
    if file.size > MAX_LOGO_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'A logo deve ter no máximo {MAX_LOGO_SIZE_MB} MB.')


class Company(BaseModel):
    """Dados e marca do negócio desta instalação. Existe um único registro."""

    id_company = models.BigAutoField(
        primary_key=True,
        db_column='id_company'
    )
    tx_name = models.CharField(
        'nome',
        max_length=150,
        db_column='tx_name'
    )
    tx_cnpj = models.CharField(
        'CNPJ',
        max_length=18,
        blank=True,
        db_column='tx_cnpj'
    )
    tx_phone = models.CharField(
        'telefone',
        max_length=20,
        blank=True,
        db_column='tx_phone'
    )
    tx_email = models.EmailField(
        'e-mail',
        max_length=128,
        blank=True,
        db_column='tx_email'
    )
    tx_address = models.CharField(
        'endereço',
        max_length=255,
        blank=True,
        db_column='tx_address'
    )
    im_logo = models.ImageField(
        'logo',
        upload_to='company/',
        blank=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'webp']), validate_logo_size],
        db_column='im_logo'
    )
    tx_primary_color = models.CharField(
        'cor principal',
        max_length=7,
        default='#1E40AF',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Use uma cor no formato #RRGGBB.')],
        db_column='tx_primary_color'
    )

    class Meta:
        verbose_name = 'empresa'

    def __str__(self):
        return self.tx_name

    def save(self, *args, **kwargs):
        self.pk = SINGLETON_ID
        previous = Company.objects.filter(pk=SINGLETON_ID).first()
        super().save(*args, **kwargs)
        if previous and previous.im_logo and previous.im_logo != self.im_logo:
            previous.im_logo.delete(save=False)

    @classmethod
    def load(cls):
        company, _ = cls.objects.get_or_create(pk=SINGLETON_ID, defaults={'tx_name': 'MINHA EMPRESA'})
        return company
