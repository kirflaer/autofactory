# Generated by Django 4.0.4 on 2022-09-14 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0013_palletcollectoperation_parent_task_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='palletcollectoperation',
            name='type_collect',
            field=models.CharField(choices=[('SHIPMENT', 'SHIPMENT'), ('ACCEPTANCE', 'ACCEPTANCE')], default='ACCEPTANCE', max_length=255, verbose_name='Тип сбора'),
        ),
    ]
