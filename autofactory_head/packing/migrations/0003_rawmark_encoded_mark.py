# Generated by Django 3.2 on 2021-11-08 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0002_markingoperation_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawmark',
            name='encoded_mark',
            field=models.CharField(blank=True, default='-', max_length=500, null=True),
        ),
    ]
