# Generated by Django 3.2 on 2022-02-03 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0027_remove_externalsource_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalsource',
            name='date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата'),
        ),
    ]