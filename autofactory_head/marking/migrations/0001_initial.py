# Generated by Django 3.2 on 2021-09-30 09:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalogs', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('factory_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkingOperation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('manual_editing', models.BooleanField(default=False)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='factory_core.shiftoperation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RawMark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')),
                ('mark', models.CharField(max_length=500)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogs.device')),
            ],
        ),
        migrations.CreateModel(
            name='MarkingOperationMarks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('mark', models.CharField(max_length=500)),
                ('encoded_mark', models.CharField(max_length=500, null=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marks', to='marking.markingoperation')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.product', verbose_name='Номенклатура')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DeviceSignal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogs.device')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
