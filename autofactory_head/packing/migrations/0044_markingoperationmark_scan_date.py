# Generated by Django 4.0.4 on 2022-11-07 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0043_markingoperation_shift'),
    ]

    operations = [
        migrations.AddField(
            model_name='markingoperationmark',
            name='scan_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время сканирования'),
        ),
    ]
