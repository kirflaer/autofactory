# Generated by Django 3.2 on 2022-02-03 16:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0026_alter_externalsource_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='externalsource',
            name='date',
        ),
    ]
