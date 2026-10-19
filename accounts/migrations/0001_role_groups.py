from django.db import migrations

ROLE_GROUPS = ['Operador', 'Gerente', 'Administrador']


def create_role_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ROLE_GROUPS:
        Group.objects.get_or_create(name=name)


def remove_role_groups(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_role_groups, remove_role_groups),
    ]
