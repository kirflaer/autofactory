# Generated by Django 3.2 on 2022-02-07 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0026_alter_task_external_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskproduct',
            name='count',
            field=models.FloatField(default=0.0, verbose_name='Количество'),
        ),
    ]
