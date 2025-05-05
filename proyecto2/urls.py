"""
URL configuration for proyectoprueba project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from proyectoApp import views

from proyectoApp.views import (
    # 📋 LISTADOS
    ListadoProyectoNuevo, ListadoCategoriaNuevo, ListadoAdquisiciones, ListadoEquiposConstruccion, ListadoManoObra, ListadoMaterialesOtros, ListadoEspecificoCategoria, ListadoContratoSubcontrato, 
    ListadoCotizacionMateriales, ListadoStaffEnami, ListadoDatosEP, ListadoDatosOtrosEP, ListadoCantidades, ListadoIngenieriaDetallesContraparte, ListadoGestionPermisos, ListadoDueno, ListadoMB, 
    ListadoAdministracionSupervision, ListadoPersonalIndirectoContratista, ListadoServiciosApoyo, ListadoOtrosADM, ListadoAdministrativoFinanciero,

    # ➕ CREACIÓN
    CrearProyectoNuevo, CrearCategoriaNuevo, CrearAdquisiciones, CrearMaterialesOtros, CrearEquiposConstruccion, CrearManoObra, CrearAPUGeneral, CrearAPUEspecifico, CrearEspecificoCategoria, 
    CrearStaffEnami, CrearDatosEP, CrearDatosOtrosEP, CrearIngenieriaDetallesContraparte, CrearGestionPermisos, CrearDueno, CrearMB, CrearAdministracionSupervision, CrearPersonalIndirectoContratista, 
    CrearServiciosApoyo, CrearOtrosADM, CrearAdministrativoFinanciero,

    # 🔄 ACTUALIZACIÓN
    ActualizarProyectoNuevo, ActualizarAPUGeneral, ActualizarAPUEspecifico, ActualizarCategoriaNuevo, ActualizarAdquisiciones, ActualizarMaterialesOtros, ActualizarEquiposConstruccion, ActualizarManoObra, 
    ActualizarEspecificoCategoria, ActualizarStaffEnami, ActualizarDatosEP, ActualizarDatosOtrosEP, ActualizarCantidades, ActualizarContratoSubcontrato, ActualizarCotizacionMateriales, 
    ActualizarIngenieriaDetallesContraparte, ActualizarGestionPermisos, ActualizarDueno, ActualizarMB, ActualizarAdministracionSupervision, ActualizarPersonalIndirectoContratista, ActualizarServiciosApoyo, 
    ActualizarOtrosADM, ActualizarAdministrativoFinanciero,

    # ❌ ELIMINACIÓN
     EliminarProyectoNuevo, EliminarAPUGeneral, EliminarAPUEspecifico, EliminarEspecificoCategoria, EliminarStaffEnami, eliminar_material, eliminar_categoria, eliminar_adquisicion, eliminar_equipo_construccion, 
     eliminar_mano_obra, eliminar_especifico_categoria, eliminar_staff_enami, eliminar_cantidad, eliminar_contrato_subcontrato, eliminar_cotizacion_materiales, eliminar_ingenieria_detalles_contraparte, 
     eliminar_gestion_permisos, eliminar_dueno, eliminar_mb, eliminar_administracion_supervision, eliminar_personal_indirecto_contratista, eliminar_servicios_apoyo, eliminar_otros_adm, eliminar_administrativo_financiero, 
     eliminar_datos_ep, eliminar_datos_otros_ep,

    # ⚙️ OTROS
    obtener_comparacion_costos, obtener_proyecto_relacionado, detalle_proyecto, obtener_subcategorias, subir_archivo, listar_proyectos, categorias_raiz_json, exportar_excel, 
)



urlpatterns = [

 # 📌 Admin y DataWizard
    path('admin/', admin.site.urls),
    path('datawizard/', include('data_wizard.urls')),

    # 📂 Carga de datos y archivos
    path('cargar_datos/', views.cargar_datos, name='cargar_datos'),
    path('subir_archivo/', subir_archivo, name='subir_archivo'),

    # 🏠 Página de inicio
    path('', views.Inicio, name='inicio'),

    # 📊 Tablas/Listados
    path('tabla_proyecto_nuevo/', views.ListadoProyectoNuevo.as_view(), name='tabla_proyecto_nuevo'),
    path('tabla_categoria_nuevo/', views.ListadoCategoriaNuevo.as_view(), name='tabla_categoria_nuevo'),
    path('tabla_adquisiciones/', views.ListadoAdquisiciones.as_view(), name='tabla_adquisiciones'),
    path('tabla_materiales_otros/', views.ListadoMaterialesOtros.as_view(), name='tabla_materiales_otros'),
    path('tabla_equipos_construccion/', views.ListadoEquiposConstruccion.as_view(), name='tabla_equipos_construccion'),
    path('tabla_mano_obra/', views.ListadoManoObra.as_view(), name='tabla_mano_obra'),
    path('tabla_apu_general/', views.ListadoAPUGeneral.as_view(), name='tabla_apu_general'),
    path('tabla_apu_especifico/', views.ListadoAPUEspecifico.as_view(), name='tabla_apu_especifico'),
    path('tabla_especifico_categoria/', views.ListadoEspecificoCategoria.as_view(), name='tabla_especifico_categoria'),
    path('tabla_staff_enami/', views.ListadoStaffEnami.as_view(), name='tabla_staff_enami'),
    path('tabla_datos_ep/', views.ListadoDatosEP.as_view(), name='tabla_datos_ep'),
    path('tabla_datos_otros_ep/', views.ListadoDatosOtrosEP.as_view(), name='tabla_datos_otros_ep'),
    path('tabla_cantidades/', views.ListadoCantidades.as_view(), name='tabla_cantidades'),
    path('tabla_cotizacion_materiales/', views.ListadoCotizacionMateriales.as_view(), name='tabla_cotizacion_materiales'),
    path('tabla_contrato_subcontrato/', views.ListadoContratoSubcontrato.as_view(), name='tabla_contrato_subcontrato'),
    path('tabla_ingenieria_detalles_contraparte/', views.ListadoIngenieriaDetallesContraparte.as_view(), name='tabla_ingenieria_detalles_contraparte'),
    path('tabla_gestion_permisos/', views.ListadoGestionPermisos.as_view(), name='tabla_gestion_permisos'),
    path('tabla_dueno/', views.ListadoDueno.as_view(), name='tabla_dueno'),
    path('tabla_administracion_supervision/', views.ListadoAdministracionSupervision.as_view(), name='tabla_administracion_supervision'),
    path('tabla_personal_indirecto_contratista/', views.ListadoPersonalIndirectoContratista.as_view(), name='tabla_personal_indirecto_contratista'),
    path('tabla_servicios_apoyo/', views.ListadoServiciosApoyo.as_view(), name='tabla_servicios_apoyo'),
    path('tabla_otros_adm/', views.ListadoOtrosADM.as_view(), name='tabla_otros_adm'),
    path('tabla_administrativo_financiero/', views.ListadoAdministrativoFinanciero.as_view(), name='tabla_administrativo_financiero'),
    path('tabla_mb/', views.ListadoMB.as_view(), name='tabla_mb'),

    # ➕ Crear
    path('crear_proyecto_nuevo/', views.CrearProyectoNuevo.as_view(), name='crear_proyecto_nuevo'),
    path('crear_categoria_nuevo/', views.CrearCategoriaNuevo.as_view(), name='crear_categoria_nuevo'),
    path('crear_adquisicion/', views.CrearAdquisiciones.as_view(), name='crear_adquisicion'),
    path('crear_materiales_otros/', views.CrearMaterialesOtros.as_view(), name='crear_materiales_otros'),
    path('crear_equipos_construccion/', views.CrearEquiposConstruccion.as_view(), name='crear_equipos_construccion'),
    path('crear_mano_obra/', views.CrearManoObra.as_view(), name='crear_mano_obra'),
    path('crear_apu_general/', views.CrearAPUGeneral.as_view(), name='crear_apu_general'),
    path('crear_apu_especifico/', views.CrearAPUEspecifico.as_view(), name='crear_apu_especifico'),
    path('crear_especifico_categoria/', views.CrearEspecificoCategoria.as_view(), name='crear_especifico_categoria'),
    path('crear_staff_enami/', views.CrearStaffEnami.as_view(), name='crear_staff_enami'),
    path('crear_datos_ep/', views.CrearDatosEP.as_view(), name='crear_datos_ep'),
    path('crear_datos_otros_ep/', views.CrearDatosOtrosEP.as_view(), name='crear_datos_otros_ep'),
    path('crear_cantidades/', views.CrearCantidades.as_view(), name='crear_cantidades'),
    path('crear_contrato_subcontrato/', views.CrearContratoSubcontrato.as_view(), name='crear_contrato_subcontrato'),
    path('crear_cotizacion_materiales/', views.CrearCotizacionMateriales.as_view(), name='crear_cotizacion_materiales'),
    path('crear_ingenieria_detalles_contraparte/', views.CrearIngenieriaDetallesContraparte.as_view(), name='crear_ingenieria_detalles_contraparte'),
    path('crear_gestion_permisos/', views.CrearGestionPermisos.as_view(), name='crear_gestion_permisos'),
    path('crear_dueno/', views.CrearDueno.as_view(), name='crear_dueno'),
    path('crear_administracion_supervision/', views.CrearAdministracionSupervision.as_view(), name='crear_administracion_supervision'),
    path('crear_personal_indirecto_contratista/', views.CrearPersonalIndirectoContratista.as_view(), name='crear_personal_indirecto_contratista'),
    path('crear_servicios_apoyo/', views.CrearServiciosApoyo.as_view(), name='crear_servicios_apoyo'),
    path('crear_otros_adm/', views.CrearOtrosADM.as_view(), name='crear_otros_adm'),
    path('crear_administrativo_financiero/', views.CrearAdministrativoFinanciero.as_view(), name='crear_administrativo_financiero'),
    path('crear_mb/', views.CrearMB.as_view(), name='crear_mb'),

    # ✏️ Actualizar
    path('actualizar_proyecto_nuevo/<str:pk>/', views.ActualizarProyectoNuevo.as_view(), name='actualizar_proyecto_nuevo'),
    path('actualizar_apu_general/<str:pk>/', views.ActualizarAPUGeneral.as_view(), name='actualizar_apu_general'),
    path('actualizar_apu_especifico/<str:pk>/', views.ActualizarAPUEspecifico.as_view(), name='actualizar_apu_especifico'),
    path('editar-categoria/<str:pk>/', ActualizarCategoriaNuevo.as_view(), name='editar_categoria_nuevo'),
    path('editar-cantidad/<str:pk>/', ActualizarCantidades.as_view(), name='editar_cantidad'),
    path('editar-adquisicion/<str:pk>/', ActualizarAdquisiciones.as_view(), name='editar_adquisicion'),
    path('editar-material-otro/<str:pk>/', ActualizarMaterialesOtros.as_view(), name='editar_material_otro'),
    path('editar-equipo-construccion/<str:pk>/', ActualizarEquiposConstruccion.as_view(), name='editar_equipo_construccion'),
    path('editar-mano-obra/<str:pk>/', ActualizarManoObra.as_view(), name='editar_mano_obra'),
    path('editar-especifico-categoria/<str:pk>/', ActualizarEspecificoCategoria.as_view(), name='editar_especifico_categoria'),
    path('editar-staff-enami/<str:pk>/', ActualizarStaffEnami.as_view(), name='editar_staff_enami'),
    path('editar-contrato-subcontrato/<str:pk>/', ActualizarContratoSubcontrato.as_view(), name='editar_contrato_subcontrato'),
    path('editar-cotizacion-materiales/<str:pk>/', ActualizarCotizacionMateriales.as_view(), name='editar_cotizacion_materiales'),
    path('editar-ingenieria-detalles-contraparte/<str:pk>/', ActualizarIngenieriaDetallesContraparte.as_view(), name='editar_ingenieria_detalles_contraparte'),
    path('editar-gestion-permisos/<str:pk>/', ActualizarGestionPermisos.as_view(), name='editar_gestion_permisos'),
    path('editar-dueno/<str:pk>/', ActualizarDueno.as_view(), name='editar_dueno'),
    path('editar-mb/<str:pk>/', ActualizarMB.as_view(), name='editar_mb'),
    path('editar-administracion-supervision/<str:pk>/', ActualizarAdministracionSupervision.as_view(), name='editar_administracion_supervision'),
    path('editar-personal-indirecto-contratista/<str:pk>/', ActualizarPersonalIndirectoContratista.as_view(), name='editar_personal_indirecto_contratista'),
    path('editar-servicios-apoyo/<str:pk>/', ActualizarServiciosApoyo.as_view(), name='editar_servicios_apoyo'),
    path('editar-otros-adm/<str:pk>/', ActualizarOtrosADM.as_view(), name='editar_otros_adm'),
    path('editar-administrativo-financiero/<str:pk>/', ActualizarAdministrativoFinanciero.as_view(), name='editar_administrativo_financiero'),
    path('editar-datos-ep/<str:pk>/', ActualizarDatosEP.as_view(), name='editar_datos_ep'),
    path('editar-datos-otros-ep/<str:pk>/', ActualizarDatosOtrosEP.as_view(), name='editar_datos_otros_ep'),

    # ❌ Eliminar (clásico .as_view)
    path('eliminar_proyecto_nuevo/<str:pk>/', views.EliminarProyectoNuevo.as_view(), name='eliminar_proyecto_nuevo'),
    path('eliminar_apu_general/<str:pk>/', views.EliminarAPUGeneral.as_view(), name='eliminar_apu_general'),
    path('eliminar_apu_epecifico/<str:pk>/', views.EliminarAPUEspecifico.as_view(), name='eliminar_apu_especifico'),
    path('eliminar-cantidad/', eliminar_cantidad, name='eliminar_cantidad'),
    path('eliminar-datos-ep/', eliminar_datos_ep, name='eliminar_datos_ep'),
    path('eliminar-datos-otros-ep/', eliminar_datos_otros_ep, name='eliminar_datos_otros_ep'),
    path('eliminar-material/', eliminar_material, name='eliminar_material'),
    path("eliminar-categoria/", eliminar_categoria, name="eliminar_categoria"),
    path("eliminar-adquisicion/", eliminar_adquisicion, name="eliminar_adquisicion"),
    path("eliminar-equipo-construccion/", eliminar_equipo_construccion, name="eliminar_equipo_construccion"),
    path("eliminar-mano-obra/", eliminar_mano_obra, name="eliminar_mano_obra"),
    path("eliminar-especifico/", eliminar_especifico_categoria, name="eliminar_especifico"),
    path("eliminar-staff-enami/", eliminar_staff_enami, name="eliminar_staff_enami"),
    path("eliminar-cotizacion-materiales/", eliminar_cotizacion_materiales, name="eliminar_cotizacion_materiales"),
    path("eliminar-contrato-subcontrato/", eliminar_contrato_subcontrato, name="eliminar_contrato_subcontrato"),
    path("eliminar-ingenieria-detalles-contraparte/", eliminar_ingenieria_detalles_contraparte, name="eliminar_ingenieria_detalles_contraparte"),
    path("eliminar-gestion-permisos/", eliminar_gestion_permisos, name="eliminar_gestion_permisos"),
    path("eliminar-dueno/", eliminar_dueno, name="eliminar_dueno"),
    path("eliminar-mb/", eliminar_mb, name="eliminar_mb"),
    path("eliminar-administracion-supervision/", eliminar_administracion_supervision, name="eliminar_administracion_supervision"),
    path("eliminar-personal-indirecto-contratista/", eliminar_personal_indirecto_contratista, name="eliminar_personal_indirecto_contratista"),
    path("eliminar-servicios-apoyo/", eliminar_servicios_apoyo, name="eliminar_servicios_apoyo"),
    path("eliminar-otros-adm/", eliminar_otros_adm, name="eliminar_otros_adm"),
    path("eliminar-administrativo-financiero/", eliminar_administrativo_financiero, name="eliminar_administrativo_financiero"),
    path('eliminar-categorias-masivo/', views.eliminar_categorias_masivo, name='eliminar_categorias_masivo'),

    # 🔍 Detalle / APIs
    path('proyecto/<str:proyecto_id>/', detalle_proyecto, name='detalle_proyecto'),
    path('api/subcategorias/<str:categoria_id>/', obtener_subcategorias, name='obtener_subcategorias'),
    path('api/categorias-raiz/<str:proyecto_id>/', categorias_raiz_json, name='categorias-raiz-json'),
    path('api/listar-proyectos/', listar_proyectos, name='listar-proyectos-json'),
    path('exportar-excel/<str:modelo_nombre>/', exportar_excel, name='exportar_excel'),
    path('api/obtener-comparacion-costos/<str:proyecto_id>/', views.obtener_comparacion_costos, name='obtener_comparacion_costos'),
    path('obtener_proyecto_relacionado/<str:proyecto_id>/', views.obtener_proyecto_relacionado, name='obtener_proyecto_relacionado'),
    path('api/duplicar-proyecto/<str:proyecto_id>/', views.duplicar_proyecto, name='duplicar_proyecto'),
    path('api/obtener-niveles-proyecto/<str:proyecto_id>/', views.obtener_niveles_proyecto, name='obtener_niveles_proyecto'),

]

