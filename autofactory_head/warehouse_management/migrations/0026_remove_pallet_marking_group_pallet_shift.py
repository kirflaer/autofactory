# Generated by Django 4.0.4 on 2022-10-27 21:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('factory_core', '0001_initial'),
        ('warehouse_management', '0025_operationproduct_count_fact_inventoryoperation'),
    ]

    operations = [
        migrations.AddField(
            model_name='pallet',
            name='shift',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='factory_core.shift', verbose_name='Смена'),
        ),
    ]
