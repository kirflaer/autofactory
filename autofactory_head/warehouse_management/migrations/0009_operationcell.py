# Generated by Django 4.0.4 on 2022-08-17 14:51

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0047_alter_externalsource_external_key_and_more'),
        ('warehouse_management', '0008_alter_orderoperation_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperationCell',
            fields=[
                ('guid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('operation', models.UUIDField(null=True, verbose_name='ГУИД операции')),
                ('type_operation', models.CharField(max_length=100, null=True, verbose_name='Тип операции')),
                ('number_operation', models.CharField(max_length=100, null=True, verbose_name='Номер операции')),
                ('external_source', models.CharField(max_length=100, null=True, verbose_name='Наименование внешнего источника')),
                ('weight', models.FloatField(default=0.0, verbose_name='Вес')),
                ('count', models.PositiveIntegerField(default=0.0, verbose_name='Количество')),
                ('cell_destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalogs.storagecell', verbose_name='Измененная ячейка')),
                ('cell_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operation_cell', to='catalogs.storagecell', verbose_name='Складская ячейка')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogs.product', verbose_name='Номенклатура')),
            ],
            options={
                'verbose_name': 'Складские ячейки операции',
                'verbose_name_plural': 'Складские ячейки операций',
            },
        ),
    ]