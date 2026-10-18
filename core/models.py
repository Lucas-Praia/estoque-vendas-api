from django.db import models


class BaseModel(models.Model):
    dt_created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True,
        db_column='dt_created_at'
    )
    dt_modified_at = models.DateTimeField(
        'alterado em',
        auto_now=True,
        db_column='dt_modified_at'
    )

    class Meta:
        abstract = True

    @classmethod
    def uppercase_fields(cls):
        """Campos de texto livre. E-mail e campos com opções ficam como estão."""
        return [
            field.attname
            for field in cls._meta.concrete_fields
            if isinstance(field, (models.CharField, models.TextField))
            and not isinstance(field, models.EmailField)
            and not field.choices
        ]

    def clean(self):
        super().clean()
        self._uppercase_texts()

    def save(self, *args, **kwargs):
        self._uppercase_texts()
        super().save(*args, **kwargs)

    def _uppercase_texts(self):
        for field_name in self.uppercase_fields():
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.upper())
