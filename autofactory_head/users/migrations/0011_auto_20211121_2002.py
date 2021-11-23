# Generated by Django 3.2 on 2021-11-21 13:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0011_device_empty_mark_reg_exp'),
        ('users', '0010_rename_settings_setting'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='vision_controller_address',
        ),
        migrations.RemoveField(
            model_name='user',
            name='vision_controller_port',
        ),
        migrations.AddField(
            model_name='setting',
            name='pallet_passport_template',
            field=models.TextField(blank=True, verbose_name='Шаблон паллетного паспорта'),
        ),
        migrations.AddField(
            model_name='setting',
            name='use_organization',
            field=models.BooleanField(default=False, verbose_name='Использовать организацию'),
        ),
        migrations.AddField(
            model_name='user',
            name='vision_controller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vision_controller', to='catalogs.device', verbose_name='Контр. тех. зрения'),
        ),
        migrations.AlterField(
            model_name='setting',
            name='name',
            field=models.CharField(blank=True, default='base settings', max_length=100),
        ),
    ]