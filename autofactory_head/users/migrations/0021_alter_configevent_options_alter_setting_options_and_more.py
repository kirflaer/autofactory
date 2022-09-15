# Generated by Django 4.0.4 on 2022-08-29 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_user_shop'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='configevent',
            options={'verbose_name': 'Настройка событий логирования', 'verbose_name_plural': 'Настройка событий логирования'},
        ),
        migrations.AlterModelOptions(
            name='setting',
            options={'verbose_name': 'Настройки пользователя', 'verbose_name_plural': 'Настройки пользователя'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ('username',), 'verbose_name': 'Пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
    ]