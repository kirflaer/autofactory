# Generated by Django 4.0.4 on 2023-07-07 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0063_alter_palletcollectoperation_type_collect_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='storagearea',
            name='allow_movement',
            field=models.BooleanField(default=False, verbose_name='Разрешить перемещение между ячейками'),
        ),
    ]
