# Generated by Django 4.0.4 on 2022-06-18 22:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0044_storagecell_alter_activationkey_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='storage',
            options={'verbose_name': 'Склад', 'verbose_name_plural': 'Склады'},
        ),
    ]