# Generated by Django 3.2 on 2021-11-21 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0013_alter_device_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='mode',
            field=models.CharField(choices=[('VISION_CONTROLLER', 'VISION_CONTROLLER'), ('VISION_CONTROLLER', 'VISION_CONTROLLER'), ('VISION_CONTROLLER', 'VISION_CONTROLLER'), ('VISION_CONTROLLER', 'VISION_CONTROLLER')], default='VISION_CONTROLLER', max_length=255),
        ),
    ]
