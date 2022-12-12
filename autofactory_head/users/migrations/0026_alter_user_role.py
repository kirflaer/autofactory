# Generated by Django 4.0.4 on 2022-11-22 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_alter_user_default_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('VISION_OPERATOR', 'VISION_OPERATOR'), ('PACKER', 'PACKER'), ('PALLET_COLLECTOR', 'PALLET_COLLECTOR'), ('REJECTER', 'REJECTER'), ('SERVICE', 'SERVICE'), ('LOADER', 'LOADER'), ('STOREKEEPER', 'STOREKEEPER')], default='PACKER', max_length=255, verbose_name='Роль'),
        ),
    ]