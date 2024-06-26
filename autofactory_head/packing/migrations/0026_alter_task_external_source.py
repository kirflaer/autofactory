# Generated by Django 3.2 on 2022-02-02 17:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0024_externalsource'),
        ('packing', '0025_markingoperation_external_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='external_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.externalsource', verbose_name='Внешний источник'),
        ),
    ]
