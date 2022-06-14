# Generated by Django 4.0.4 on 2022-06-14 08:38

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0043_storage_store_semi_product'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse_management', '0003_movementoperation_production_date_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MovementOperation',
            new_name='AcceptanceOperation',
        ),
        migrations.AlterModelOptions(
            name='acceptanceoperation',
            options={'verbose_name': 'Приемка на склад', 'verbose_name_plural': 'Операции приемки товаров'},
        ),
    ]