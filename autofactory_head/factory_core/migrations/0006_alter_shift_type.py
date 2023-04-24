# Generated by Django 4.0.4 on 2023-04-24 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('factory_core', '0005_alter_shift_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='type',
            field=models.CharField(choices=[('MARKED', 'Marked'), ('UNMARKED', 'Unmarked'), ('SEMI_PRODUCTS', 'Semi Products')], default='MARKED', max_length=20, null=True, verbose_name='Тип'),
        ),
    ]
