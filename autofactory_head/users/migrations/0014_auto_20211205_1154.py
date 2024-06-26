# Generated by Django 3.2 on 2021-12-05 04:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_auto_20211203_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='collect_pallet_mode_is_active',
            field=models.BooleanField(default=True, verbose_name='Доступен режим сбора паллет'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_local_admin',
            field=models.BooleanField(default=False, verbose_name='Локальный администратор'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('VISION_OPERATOR', 'VISION_OPERATOR'), ('PACKER', 'PACKER'), ('PALLET_COLLECTOR', 'PALLET_COLLECTOR'), ('REJECTER', 'REJECTER'), ('SERVICE', 'SERVICE')], default='PACKER', max_length=255, verbose_name='Роль'),
        ),
        migrations.CreateModel(
            name='ServiceEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_event', models.CharField(choices=[('SERVICE', 'SERVICE'), ('CUSTOM', 'CUSTOM'), ('TABLET', 'TABLET')], default='CUSTOM', max_length=255, verbose_name='Тип события')),
                ('argument', models.CharField(max_length=255, verbose_name='Параметр')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
        ),
    ]
