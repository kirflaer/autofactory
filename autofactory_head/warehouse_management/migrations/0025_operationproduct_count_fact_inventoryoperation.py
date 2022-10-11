# Generated by Django 4.0.4 on 2022-10-10 12:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0049_product_not_marked_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse_management', '0024_arrivalatstockoperation'),
    ]

    operations = [
        migrations.AddField(
            model_name='operationproduct',
            name='count_fact',
            field=models.PositiveIntegerField(default=0.0, verbose_name='Количество факт (для операций сбора)'),
        ),
        migrations.CreateModel(
            name='InventoryOperation',
            fields=[
                ('unloaded', models.BooleanField(default=False, verbose_name='Выгружена')),
                ('ready_to_unload', models.BooleanField(default=False, verbose_name='Готова к выгрузке')),
                ('closed', models.BooleanField(default=False, verbose_name='Закрыта')),
                ('number', models.IntegerField(default=1)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('NEW', 'New'), ('WORK', 'Work'), ('WAIT', 'Wait'), ('CLOSE', 'Close')], default='NEW', max_length=255, verbose_name='Статус')),
                ('external_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.externalsource', verbose_name='Внешний источник')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Инвентаризация',
                'verbose_name_plural': 'Инвентаризация',
            },
        ),
    ]
