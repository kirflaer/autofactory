# Generated by Django 3.2 on 2022-03-15 08:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0034_reg_exp_empty_marks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='empty_mark_reg_exp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.regularexpression', verbose_name='Регулярное выражение пустого пакета'),
        ),
        migrations.AlterField(
            model_name='regularexpression',
            name='type_expression',
            field=models.CharField(choices=[('AGGREGATON_CODE', 'AGGREGATON_CODE'), ('MARK', 'MARK'), ('EMPTY_DATA_STREAM', 'EMPTY_DATA_STREAM')], default='AGGREGATON_CODE', max_length=255),
        ),
    ]
