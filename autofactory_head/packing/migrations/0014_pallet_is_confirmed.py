# Generated by Django 3.2 on 2021-12-16 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0013_auto_20211216_1803'),
    ]

    operations = [
        migrations.AddField(
            model_name='pallet',
            name='is_confirmed',
            field=models.BooleanField(default=False, verbose_name='Подтверждена'),
        ),
    ]
