# Generated by Django 5.1.5 on 2025-03-13 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectoApp', '0007_contratosubcontrato_cotizacionmateriales'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archivosubido',
            name='modelo_destino',
            field=models.CharField(choices=[('ProyectoNuevo', 'Proyecto Nuevo'), ('CategoriaNuevo', 'Categoría Nueva'), ('CostoNuevo', 'Costo Nuevo'), ('Adquisiciones', 'Adquisiciones'), ('Cantidades', 'Cantidades'), ('MaterialesOtros', 'Materiales Otros'), ('EquiposConstruccion', 'Equipos Construcción'), ('ManoObra', 'Mano Obra'), ('EspecificoCategoria', 'Especifico Categoria'), ('ApuEspecifico', 'Apu Especifico'), ('ApuGeneral', 'Apu General'), ('StaffEnami', 'Staff Enami'), ('ContratoSubcontrato', 'Contrato Subcontrato'), ('CotizacionMateriales', 'Cotizacion Materiales')], max_length=50),
        ),
        migrations.AlterField(
            model_name='cotizacionmateriales',
            name='cotizacion',
            field=models.CharField(max_length=100),
        ),
    ]
