# Generated by Django 3.2 on 2022-01-14 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0021_auto_20220113_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='external_source',
            field=models.CharField(blank=True, max_length=255, verbose_name='Источник внешней системы'),
        ),
    ]