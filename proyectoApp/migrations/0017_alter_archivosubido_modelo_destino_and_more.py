# Generated by Django 5.1.5 on 2025-03-19 20:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectoApp', '0016_alter_archivosubido_modelo_destino_otrosadm_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='archivosubido',
            name='modelo_destino',
            field=models.CharField(choices=[('ProyectoNuevo', 'Proyecto Nuevo'), ('CategoriaNuevo', 'Categoría Nueva'), ('CostoNuevo', 'Costo Nuevo'), ('Adquisiciones', 'Adquisiciones'), ('Cantidades', 'Cantidades'), ('MaterialesOtros', 'Materiales Otros'), ('EquiposConstruccion', 'Equipos Construcción'), ('ManoObra', 'Mano Obra'), ('EspecificoCategoria', 'Especifico Categoria'), ('ApuEspecifico', 'Apu Especifico'), ('ApuGeneral', 'Apu General'), ('StaffEnami', 'Staff Enami'), ('ContratoSubcontrato', 'Contrato Subcontrato'), ('CotizacionMateriales', 'Cotizacion Materiales'), ('IngenieriaDetallesContraparte', 'Ingenieria Detalles Contraparte'), ('GestionPermisos', 'Gestion Permisos'), ('Dueno', 'Dueño'), ('MB', 'MB'), ('AdministracionSupervision', 'Administracion Supervision'), ('PersonalIndirectoContratista', 'Personal Indirecto Contratista'), ('ServiciosApoyo', 'Servicios Apoyo'), ('OtrosADM', 'Otros ADM'), ('AdministrativoFinanciero', 'Administrativo Financiero')], max_length=50),
        ),
        migrations.CreateModel(
            name='AdministrativoFinanciero',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('unidad', models.CharField(max_length=255)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=12)),
                ('meses', models.IntegerField()),
                ('sobre_contrato_base', models.DecimalField(decimal_places=2, max_digits=5)),
                ('costo_total', models.DecimalField(decimal_places=2, max_digits=15)),
                ('id_categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='administrativo_financiero', to='proyectoApp.categorianuevo')),
            ],
        ),
    ]
