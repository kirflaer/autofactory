# Generated by Django 4.0.4 on 2023-07-27 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0066_pallet_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='pallet',
            name='initial_count',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Количество ящиков'),
        ),
    ]
