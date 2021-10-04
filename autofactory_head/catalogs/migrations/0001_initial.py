# Generated by Django 3.2 on 2021-09-30 09:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_key', models.CharField(blank=True, max_length=36)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_key', models.CharField(blank=True, max_length=36)),
                ('polling_interval', models.PositiveIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_key', models.CharField(blank=True, max_length=36)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_key', models.CharField(blank=True, max_length=36)),
                ('gtin', models.CharField(blank=True, default='', max_length=200, verbose_name='GTIN')),
                ('vendor_code', models.CharField(blank=True, default='', max_length=50, verbose_name='Артикул')),
                ('sku', models.CharField(blank=True, default='', max_length=50)),
                ('expiration_date', models.PositiveIntegerField(default=0, verbose_name='Срок годности')),
                ('count_in_pallet', models.PositiveIntegerField(default=0, verbose_name='Количество в паллете')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_key', models.CharField(blank=True, max_length=36)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Line',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogs.department')),
                ('device', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.device')),
                ('storage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogs.storage')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
