# Generated by Django 4.0.4 on 2022-09-29 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packing', '0033_markingoperation_group_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markingoperation',
            name='group_offline',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Ключ группы оффлайн'),
        ),
    ]
