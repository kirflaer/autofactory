# Generated by Django 4.0.4 on 2022-08-16 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse_management', '0005_alter_pallet_status_palletsource'),
    ]

    operations = [
        migrations.RenameField(
            model_name='operationcell',
            old_name='changed_cell',
            new_name='cell_destination',
        ),
        migrations.RenameField(
            model_name='operationcell',
            old_name='cell',
            new_name='cell_source',
        ),
        migrations.AlterField(
            model_name='pallet',
            name='status',
            field=models.CharField(choices=[('COLLECTED', 'Collected'), ('CONFIRMED', 'Confirmed'), ('POSTED', 'Posted'), ('SHIPPED', 'Shipped'), ('ARCHIVED', 'Archived'), ('WAITED', 'Waited')], default='COLLECTED', max_length=20, verbose_name='Статус'),
        ),
    ]
