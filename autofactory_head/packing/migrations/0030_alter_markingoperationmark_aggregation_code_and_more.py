# Generated by Django 4.0.4 on 2022-06-10 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0029_remove_palletcode_pallet_remove_task_client_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markingoperationmark',
            name='aggregation_code',
            field=models.CharField(max_length=500, null=True, verbose_name='Код агрегации'),
        ),
        migrations.AlterField(
            model_name='markingoperationmark',
            name='encoded_mark',
            field=models.CharField(max_length=500, null=True, verbose_name='Зашифрованная марка'),
        ),
        migrations.AlterField(
            model_name='markingoperationmark',
            name='mark',
            field=models.CharField(max_length=500, verbose_name='Марка'),
        ),
    ]
