# Generated by Django 4.0.4 on 2023-07-11 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0064_storagearea_allow_movement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pallet',
            name='status',
            field=models.CharField(choices=[('NEW', 'New'), ('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited'), ('FOR_SHIPMENT', 'For Shipment'), ('SELECTED', 'Selected'), ('PLACED', 'Placed'), ('FOR_REPACKING', 'For Repacking'), ('FOR_PLACED', 'For Placed'), ('PRE_FOR_SHIPMENT', 'Pre For Shipment')], default='NEW', max_length=20, verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='storagearea',
            name='new_status_on_admission',
            field=models.CharField(choices=[('NEW', 'New'), ('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited'), ('FOR_SHIPMENT', 'For Shipment'), ('SELECTED', 'Selected'), ('PLACED', 'Placed'), ('FOR_REPACKING', 'For Repacking'), ('FOR_PLACED', 'For Placed'), ('PRE_FOR_SHIPMENT', 'Pre For Shipment')], default='SELECTED', max_length=20, verbose_name='Статус'),
        ),
    ]