# Generated by Django 3.2 on 2021-11-08 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_vision_controller_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('VISION_OPERATOR', 'VISION_OPERATOR'), ('PACKER', 'PACKER'), ('PALLET_COLLECTOR', 'PALLET_COLLECTOR'), ('REJECTER', 'REJECTER')], default='PACKER', max_length=255),
        ),
    ]
