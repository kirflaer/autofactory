# Generated by Django 4.0.4 on 2023-08-14 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0068_alter_pallet_initial_count'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='suitablepallets',
            options={'verbose_name': 'Подходящие паллеты', 'verbose_name_plural': 'Подходящие паллеты (построчная выгрузка)'},
        ),
    ]