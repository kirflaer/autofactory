# Generated by Django 3.2 on 2022-03-15 08:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0031_alter_regularexpression_type_expression'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='mark_reg_exp',
        ),
        migrations.AddField(
            model_name='device',
            name='reg_exp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.regularexpression', verbose_name='Регулярное выражение получения марки'),
        ),
        migrations.AlterField(
            model_name='regularexpression',
            name='type_expression',
            field=models.CharField(choices=[('AGGREGATON_CODE', 'AGGREGATON_CODE'), ('MARK', 'MARK')], default='AGGREGATON_CODE', max_length=255),
        ),
    ]
