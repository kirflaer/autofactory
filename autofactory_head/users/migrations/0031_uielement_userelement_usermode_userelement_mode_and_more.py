# Generated by Django 4.0.4 on 2023-04-06 10:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_user_privileged_user_alter_user_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='UIElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=155, verbose_name='Имя')),
                ('identifier', models.CharField(max_length=155, verbose_name='Идентификатор')),
            ],
            options={
                'verbose_name': 'UI элемент',
                'verbose_name_plural': 'UI элементы',
            },
        ),
        migrations.CreateModel(
            name='UserElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('element', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.uielement', verbose_name='UI элемент')),
            ],
        ),
        migrations.CreateModel(
            name='UserMode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=155, verbose_name='Имя')),
                ('elements', models.ManyToManyField(through='users.UserElement', to='users.uielement', verbose_name='Элементы интерфейса')),
            ],
            options={
                'verbose_name': 'Режим интерфейса',
                'verbose_name_plural': 'Режимы интерфейса',
            },
        ),
        migrations.AddField(
            model_name='userelement',
            name='mode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.usermode', verbose_name='Режим'),
        ),
        migrations.AddField(
            model_name='user',
            name='mode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.usermode', verbose_name='Режим'),
        ),
        migrations.AddConstraint(
            model_name='userelement',
            constraint=models.UniqueConstraint(fields=('mode', 'element'), name='unique_uni_elements'),
        ),
    ]
