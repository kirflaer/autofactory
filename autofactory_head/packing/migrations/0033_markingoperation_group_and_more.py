# Generated by Django 4.0.4 on 2022-09-28 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0032_markingoperation_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='markingoperation',
            name='group',
            field=models.UUIDField(blank=True, null=True, verbose_name='Группа'),
        ),
        migrations.AddField(
            model_name='markingoperation',
            name='group_offline',
            field=models.UUIDField(blank=True, null=True, verbose_name='Ключ группы оффлайн'),
        ),
    ]
