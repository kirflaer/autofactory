# Generated by Django 4.0.4 on 2023-01-08 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='label_sizes',
            field=models.TextField(blank=True, verbose_name='Шаблон этикетки'),
        ),
        migrations.AddField(
            model_name='setting',
            name='label_template',
            field=models.TextField(blank=True, verbose_name='Шаблон этикетки'),
        ),
    ]
