# Generated by Django 4.0.4 on 2023-01-08 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_setting_label_sizes_setting_label_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='label_sizes',
            field=models.CharField(blank=True, max_length=255, verbose_name='Размеры этикеток'),
        ),
    ]
