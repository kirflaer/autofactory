# Generated by Django 3.2 on 2022-03-17 14:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0036_gtin_in_units'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivationKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_activation', models.CharField(choices=[('PERPETUAL', 'PERPETUAL'), ('BY_DATE', 'BY_DATE')], default='PERPETUAL', max_length=255)),
                ('number', models.CharField(max_length=1024, verbose_name='Идентификатор')),
                ('date', models.CharField(blank=True, default='', max_length=1024, verbose_name='Дата завершения')),
            ],
        ),
        migrations.AlterField(
            model_name='regularexpression',
            name='type_expression',
            field=models.CharField(choices=[('AGGREGATION_CODE', 'AGGREGATION_CODE'), ('MARK', 'MARK'), ('EMPTY_DATA_STREAM', 'EMPTY_DATA_STREAM'), ('MARK_AUTO_SCANNER', 'MARK_AUTO_SCANNER')], default='AGGREGATION_CODE', max_length=255),
        ),
        migrations.AddField(
            model_name='regularexpression',
            name='activation_code',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='device', to='catalogs.activationkey', verbose_name='Код активации'),
        ),
    ]
