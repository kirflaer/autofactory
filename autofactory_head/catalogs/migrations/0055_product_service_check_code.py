# Generated by Django 4.0.4 on 2023-12-11 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0054_alter_product_options_alter_product_not_marked'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='service_check_code',
            field=models.CharField(blank=True, max_length=155, null=True, verbose_name='Внутренний код для проверки ШК'),
        ),
    ]