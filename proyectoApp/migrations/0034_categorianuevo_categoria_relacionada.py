# Generated by Django 5.1.5 on 2025-04-03 16:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectoApp', '0033_alter_manoobra_tarifa_usd_hh_equipos'),
    ]

    operations = [
        migrations.AddField(
            model_name='categorianuevo',
            name='categoria_relacionada',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categorias_comparar', to='proyectoApp.categorianuevo'),
        ),
    ]
