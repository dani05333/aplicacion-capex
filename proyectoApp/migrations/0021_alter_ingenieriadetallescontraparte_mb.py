# Generated by Django 5.1.5 on 2025-03-21 15:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectoApp', '0020_alter_gestionpermisos_mb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingenieriadetallescontraparte',
            name='MB',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='proyectoApp.mb'),
        ),
    ]
