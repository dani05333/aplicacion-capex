# Generated by Django 5.1.5 on 2025-04-07 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectoApp', '0036_rename_categoria_relacionada_id_categorianuevo_categoria_relacionada'),
    ]

    operations = [
        migrations.AddField(
            model_name='proyectonuevo',
            name='proyecto_relacionado',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
