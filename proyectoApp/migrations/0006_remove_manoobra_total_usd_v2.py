# Generated by Django 5.1.5 on 2025-03-12 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proyectoApp', '0005_materialesotros_crecimiento_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manoobra',
            name='total_usd_v2',
        ),
    ]
