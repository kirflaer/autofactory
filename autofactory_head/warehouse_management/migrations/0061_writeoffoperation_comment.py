# Generated by Django 4.0.4 on 2023-05-12 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0060_inventoryaddresswarehouseoperation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='writeoffoperation',
            name='comment',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Комментарий'),
        ),
    ]