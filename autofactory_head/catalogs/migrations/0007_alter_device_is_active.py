# Generated by Django 3.2 on 2021-10-26 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0006_auto_20211023_1512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Действует'),
        ),
    ]
