# Generated by Django 4.0.4 on 2023-04-28 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0056_alter_pallet_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='palletsource',
            name='related_task',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Идентификатор связанного задания'),
        ),
        migrations.AddField(
            model_name='palletsource',
            name='type_collect',
            field=models.CharField(choices=[('SHIPMENT', 'Shipment'), ('ACCEPTANCE', 'Acceptance'), ('SELECTION', 'Selection'), ('WRITE_OFF', 'Write Off')], default='SHIPMENT', max_length=255, verbose_name='Тип сбора'),
        ),
        migrations.AlterField(
            model_name='palletcollectoperation',
            name='type_collect',
            field=models.CharField(choices=[('SHIPMENT', 'Shipment'), ('ACCEPTANCE', 'Acceptance'), ('SELECTION', 'Selection'), ('WRITE_OFF', 'Write Off')], default='ACCEPTANCE', max_length=255, verbose_name='Тип сбора'),
        ),
    ]
