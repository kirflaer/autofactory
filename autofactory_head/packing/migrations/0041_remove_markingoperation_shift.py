# Generated by Django 4.0.4 on 2022-10-27 12:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0040_shift_author_shift_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='markingoperation',
            name='shift',
        ),
    ]