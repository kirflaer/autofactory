# Generated by Django 3.2 on 2021-10-22 06:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0002_auto_20211021_2057'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='polling_interval',
        ),
    ]
