# Generated by Django 3.2 on 2022-02-03 14:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0024_externalsource'),
    ]

    operations = [
        migrations.RenameField(
            model_name='externalsource',
            old_name='guid',
            new_name='external_key',
        ),
    ]
