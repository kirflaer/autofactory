# Generated by Django 4.0.4 on 2022-12-22 10:49

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0033_storagecell_remove_pallet_cell_alter_pallet_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StorageArea',
            fields=[
                ('name', models.CharField(max_length=1024, verbose_name='Наименование')),
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_key', models.CharField(blank=True, max_length=36, verbose_name='Внешний ключ')),
                ('new_status_on_admission', models.CharField(choices=[('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited'), ('FOR_SHIPMENT', 'For Shipment'), ('SELECTED', 'Selected'), ('PLACED', 'Placed'), ('FOR_REPACKING', 'For Repacking')], default='SELECTED', max_length=20, verbose_name='Статус')),
            ],
            options={
                'verbose_name': 'Область хранения',
                'verbose_name_plural': 'Области хранения',
            },
        ),
        migrations.AddField(
            model_name='storagecell',
            name='storage_area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='warehouse_management.storagearea', verbose_name='Область хранения'),
        ),
    ]