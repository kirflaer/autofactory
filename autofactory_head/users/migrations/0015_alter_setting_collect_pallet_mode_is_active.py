# Generated by Django 3.2 on 2021-12-05 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_auto_20211205_1154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='collect_pallet_mode_is_active',
            field=models.BooleanField(default=False, verbose_name='Доступен режим сбора паллет'),
        ),
    ]
