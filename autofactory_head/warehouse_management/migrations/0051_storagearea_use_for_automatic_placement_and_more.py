# Generated by Django 4.0.4 on 2023-03-08 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0050_storagecell_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='storagearea',
            name='use_for_automatic_placement',
            field=models.BooleanField(default=False, verbose_name='Используется для автоматического размещения'),
        ),
        migrations.AlterField(
            model_name='pallet',
            name='status',
            field=models.CharField(choices=[('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited'), ('FOR_SHIPMENT', 'For Shipment'), ('SELECTED', 'Selected'), ('PLACED', 'Placed'), ('FOR_REPACKING', 'For Repacking'), ('FOR_PLACED', 'For Placed')], default='COLLECTED', max_length=20, verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='storagearea',
            name='new_status_on_admission',
            field=models.CharField(choices=[('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited'), ('FOR_SHIPMENT', 'For Shipment'), ('SELECTED', 'Selected'), ('PLACED', 'Placed'), ('FOR_REPACKING', 'For Repacking'), ('FOR_PLACED', 'For Placed')], default='SELECTED', max_length=20, verbose_name='Статус'),
        ),
    ]