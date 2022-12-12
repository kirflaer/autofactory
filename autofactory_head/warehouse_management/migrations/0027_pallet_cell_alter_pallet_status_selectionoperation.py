# Generated by Django 4.0.4 on 2022-11-22 07:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0050_product_variable_pallet_weight'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse_management', '0026_remove_pallet_marking_group_pallet_shift'),
    ]

    operations = [
        migrations.AddField(
            model_name='pallet',
            name='cell',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalogs.storagecell', verbose_name='Ячейка'),
        ),
        migrations.AlterField(
            model_name='pallet',
            name='status',
            field=models.CharField(choices=[('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited'), ('FOR_SHIPMENT', 'For Shipment'), ('SELECTED', 'Selected')], default='COLLECTED', max_length=20, verbose_name='Статус'),
        ),
        migrations.CreateModel(
            name='SelectionOperation',
            fields=[
                ('unloaded', models.BooleanField(default=False, verbose_name='Выгружена')),
                ('ready_to_unload', models.BooleanField(default=False, verbose_name='Готова к выгрузке')),
                ('closed', models.BooleanField(default=False, verbose_name='Закрыта')),
                ('number', models.IntegerField(default=1)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('NEW', 'New'), ('WORK', 'Work'), ('WAIT', 'Wait'), ('CLOSE', 'Close')], default='NEW', max_length=255, verbose_name='Статус')),
                ('external_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.externalsource', verbose_name='Внешний источник')),
                ('parent_task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='warehouse_management.shipmentoperation', verbose_name='Родительское задание')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Отбор со склада',
                'verbose_name_plural': 'Отбор со со склада (Заявка на завод)',
            },
        ),
    ]