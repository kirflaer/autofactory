# Generated by Django 4.0.4 on 2023-01-26 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0042_palletproduct_has_divergence'),
    ]

    operations = [
        migrations.AddField(
            model_name='operationpallet',
            name='weight',
            field=models.PositiveIntegerField(blank=True, default=0, verbose_name='Вес'),
        ),
    ]