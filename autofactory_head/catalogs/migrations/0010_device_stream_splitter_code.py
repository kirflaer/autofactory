# Generated by Django 3.2 on 2021-11-15 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0009_alter_device_port'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='stream_splitter_code',
            field=models.PositiveIntegerField(default=0, verbose_name='Разделитель потока сканирования марок'),
        ),
    ]