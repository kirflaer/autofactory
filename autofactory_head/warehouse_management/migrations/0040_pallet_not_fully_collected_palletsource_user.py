# Generated by Django 4.0.4 on 2023-01-09 20:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse_management', '0039_operationpallet_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='pallet',
            name='not_fully_collected',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Собрана не полностью'),
        ),
        migrations.AddField(
            model_name='palletsource',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
