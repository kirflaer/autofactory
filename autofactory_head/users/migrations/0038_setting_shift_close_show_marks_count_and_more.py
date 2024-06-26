# Generated by Django 4.0.4 on 2023-10-01 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0037_setting_show_raw_marking'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='shift_close_show_marks_count',
            field=models.BooleanField(default=False, verbose_name='Показывать собранные марки при закрытии смены'),
        ),
        migrations.AddField(
            model_name='setting',
            name='shift_close_show_pallet_count',
            field=models.BooleanField(default=False, verbose_name='Показывать собранные паллеты при закрытии смены'),
        ),
    ]
