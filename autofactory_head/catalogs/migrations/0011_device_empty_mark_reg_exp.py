# Generated by Django 3.2 on 2021-11-15 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0010_device_stream_splitter_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='empty_mark_reg_exp',
            field=models.CharField(blank=True, max_length=150, verbose_name='Регулярное выражение пустой марки'),
        ),
    ]
