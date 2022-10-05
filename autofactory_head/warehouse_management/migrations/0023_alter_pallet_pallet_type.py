# Generated by Django 4.0.4 on 2022-10-05 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0022_alter_pallet_marking_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pallet',
            name='pallet_type',
            field=models.CharField(choices=[('SHIPPED', 'Shipped'), ('FULLED', 'Fulled'), ('COMBINED', 'Combined')], default='FULLED', max_length=50, verbose_name='Тип'),
        ),
    ]
