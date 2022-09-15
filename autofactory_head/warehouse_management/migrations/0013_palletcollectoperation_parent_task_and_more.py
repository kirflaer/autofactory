# Generated by Django 4.0.4 on 2022-09-14 15:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0012_pallet_production_shop_alter_pallet_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='palletcollectoperation',
            name='parent_task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='warehouse_management.shipmentoperation', verbose_name='Родительское задание'),
        ),
        migrations.AddField(
            model_name='palletproduct',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='warehouse_management.orderoperation', verbose_name='Заказ клиента'),
        ),
        migrations.AddField(
            model_name='palletsource',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='warehouse_management.orderoperation', verbose_name='Заказ клиента'),
        ),
    ]