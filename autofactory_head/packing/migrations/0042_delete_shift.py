# Generated by Django 4.0.4 on 2022-10-27 20:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0041_remove_markingoperation_shift'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Shift',
        ),
    ]