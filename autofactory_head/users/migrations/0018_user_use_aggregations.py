# Generated by Django 3.2 on 2022-02-16 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='use_aggregations',
            field=models.BooleanField(default=False, verbose_name='Использовать агрегацию'),
        ),
    ]
