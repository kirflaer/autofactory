# Generated by Django 4.0.4 on 2022-09-14 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0014_palletcollectoperation_type_collect'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderoperation',
            name='client_presentation',
            field=models.CharField(blank=True, default='', max_length=150, null=True, verbose_name='Клиент'),
        ),
        migrations.AddField(
            model_name='pallet',
            name='has_shipped_products',
            field=models.BooleanField(default=False, verbose_name='Содержит номенклатуру требующую обеспечения'),
        ),
        migrations.AddField(
            model_name='pallet',
            name='pallet_type',
            field=models.CharField(choices=[('SHIPPED', 'Shipped'), ('FULLED', 'Fulled'), ('COMBINED', 'Combined')], default='FULLED', max_length=50, verbose_name='Статус'),
        ),
        migrations.AddField(
            model_name='palletproduct',
            name='external_key',
            field=models.CharField(blank=True, max_length=36, null=True, verbose_name='Внешний ключ'),
        ),
        migrations.AddField(
            model_name='palletsource',
            name='external_key',
            field=models.CharField(blank=True, max_length=36, null=True, verbose_name='Внешний ключ'),
        ),
    ]
