# Generated by Django 3.2 on 2021-11-14 13:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0008_product_is_weight'),
        ('users', '0008_alter_user_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, default='-', help_text='email address', max_length=254),
        ),
        migrations.AlterField(
            model_name='user',
            name='line',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogs.line', verbose_name='Линия'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('VISION_OPERATOR', 'VISION_OPERATOR'), ('PACKER', 'PACKER'), ('PALLET_COLLECTOR', 'PALLET_COLLECTOR'), ('REJECTER', 'REJECTER')], default='PACKER', max_length=255, verbose_name='Роль'),
        ),
    ]
