# Generated by Django 3.2 on 2021-10-26 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='vision_controller_address',
            field=models.CharField(blank=True, max_length=150, verbose_name='Контроллер тех. зрения (адрес)'),
        ),
        migrations.AddField(
            model_name='user',
            name='vision_controller_port',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Контроллер тех. зрения (порт)'),
        ),
    ]
