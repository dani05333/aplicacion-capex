from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from .models import ProyectoNuevo, CategoriaNuevo, CostoNuevo, Adquisiciones, MaterialesOtros, EquiposConstruccion, ManoObra, ApuGeneral, ApuEspecifico, ArchivoSubido, EspecificoCategoria, StaffEnami, DatosOtrosEP, DatosEP, Cantidades, ContratoSubcontrato, CotizacionMateriales, IngenieriaDetallesContraparte, GestionPermisos, Dueno, MB, AdministracionSupervision, PersonalIndirectoContratista, ServiciosApoyo, OtrosADM, AdministrativoFinanciero
import os
from django.conf import settings
from .forms import ArchivoSubidoForm, ProyectoNuevoForm, CategoriaNuevoForm, CostoNuevoForm, AdquisicionesForm, MaterialesOtrosForm, EquiposConstruccionForm, ManoObraForm, APUGeneralForm, APUEspecificoForm, EspecificoCategoriaForm, StaffEnamiForm, DatosOtrosEPForm, DatosEPForm, CantidadesForm, ContratoSubcontratoForm, CotizacionMaterialesForm, IngenieriaDetallesContraparteForm, GestionPermisosForm, DuenoForm, MBForm, AdministracionSupervisionForm, PersonalIndirectoContratistaForm, ServiciosApoyoForm, OtrosADMForm, AdministrativoFinancieroForm
import pandas as pd
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import ListView, TemplateView, CreateView, UpdateView, DeleteView
from .cargar_datos import cargar_proyecto_nuevo, cargar_categoria_nueva, cargar_costo_nuevo, cargar_adquisiciones, cargar_equipos_construccion, cargar_mano_obra, cargar_materiales_otros, cargar_apu_especifico, cargar_apu_general, cargar_especifico_categoria, cargar_staff_enami, cargar_datos_ep, cargar_datos_otros_ep, cargar_cantidades, cargar_contrato_subcontrato, cargar_cotizacion_materiales, cargar_ingenieria_detalles_contraparte, cargar_gestion_permisos, cargar_dueno, cargar_mb, cargar_administracion_supervision, cargar_personal_indirecto_contratista, cargar_servicios_apoyo, cargar_otros_adm, cargar_administrativo_financiero
from django.db.models import Sum, Q, F, Subquery, OuterRef
from django.http import JsonResponse
from django.db import transaction
from django.apps import apps
from django import forms
from django.urls import reverse_lazy
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import json
from django.utils.decorators import method_decorator
import traceback
from io import BytesIO  # Importación requerida
import zipfile
from openpyxl import Workbook
import tempfile
import sys
import io
from django.template.loader import render_to_string
from functools import wraps
from django.views.decorators.http import require_POST


def obtener_proyecto_relacionado(request, proyecto_id):
    try:
        proyecto = ProyectoNuevo.objects.get(id=proyecto_id)
        if proyecto.proyecto_relacionado:
            return JsonResponse({'proyecto_relacionado': proyecto.proyecto_relacionado})
        else:
            return JsonResponse({'proyecto_relacionado': None})
    except ProyectoNuevo.DoesNotExist:
        return JsonResponse({'error': 'Proyecto no encontrado'}, status=404)
    

def comparar_costos(proyecto_id):
    try:
        proyecto = ProyectoNuevo.objects.get(id=proyecto_id)
        proyecto_relacionado = ProyectoNuevo.objects.filter(
            proyecto_relacionado=proyecto.proyecto_relacionado
        ).exclude(id=proyecto.id).first()

        if not proyecto_relacionado:
            return {
                "categorias": [],
                "costos_proyecto_2": [],
                "costos_proyecto_3": []
            }

        # Obtener categorías de ambos proyectos
        categorias_proyecto_1 = CategoriaNuevo.objects.filter(proyecto=proyecto)
        categorias_proyecto_2 = CategoriaNuevo.objects.filter(proyecto=proyecto_relacionado)

        # Relacionar categorías por `categoria_relacionada`
        relaciones_proyecto_1 = {cat.categoria_relacionada: cat for cat in categorias_proyecto_1 if cat.categoria_relacionada}
        relaciones_proyecto_2 = {cat.categoria_relacionada: cat for cat in categorias_proyecto_2 if cat.categoria_relacionada}

        comparaciones = []

        for cat_rel, cat_1 in relaciones_proyecto_1.items():
            if cat_rel in relaciones_proyecto_2:
                cat_2 = relaciones_proyecto_2[cat_rel]
                comparaciones.append({
                    'categoria': cat_1.nombre,
                    'costo_proyecto_2': cat_1.total_costo,
                    'costo_proyecto_3': cat_2.total_costo,
                    'diferencia': cat_1.total_costo - cat_2.total_costo
                })
            else:
                comparaciones.append({
                    'categoria': cat_1.nombre,
                    'costo_proyecto_2': cat_1.total_costo,
                    'costo_proyecto_3': None,
                    'diferencia': None
                })

        # Agregar categorías del segundo proyecto que no están en el primero
        for cat_rel, cat_2 in relaciones_proyecto_2.items():
            if cat_rel not in relaciones_proyecto_1:
                comparaciones.append({
                    'categoria': cat_2.nombre,
                    'costo_proyecto_2': None,
                    'costo_proyecto_3': cat_2.total_costo,
                    'diferencia': None
                })

        return comparaciones

    except ProyectoNuevo.DoesNotExist:
        return {
            "categorias": [],
            "costos_proyecto_2": [],
            "costos_proyecto_3": []
        }


def obtener_comparacion_costos(request, proyecto_id):
    try:
        # 1. Obtener parámetro de nivel si existe
        nivel = request.GET.get('nivel')
        
        # 2. Obtener proyectos
        proyecto_actual = ProyectoNuevo.objects.get(id=proyecto_id)
        
        if not proyecto_actual.proyecto_relacionado:
            return JsonResponse({'error': 'El proyecto no tiene proyecto relacionado'}, status=404)
        
        # Buscar proyectos con el mismo proyecto_relacionado (excluyendo el actual)
        proyectos_relacionados = ProyectoNuevo.objects.filter(
            proyecto_relacionado=proyecto_actual.proyecto_relacionado
        ).exclude(id=proyecto_actual.id)
        
        if not proyectos_relacionados.exists():
            return JsonResponse({'error': 'No se encontraron proyectos relacionados'}, status=404)
            
        proyecto_comparar = proyectos_relacionados.first()

        # 3. Obtener categorías con posible filtro por nivel
        categorias_actual = CategoriaNuevo.objects.filter(proyecto=proyecto_actual)
        categorias_comparar = CategoriaNuevo.objects.filter(proyecto=proyecto_comparar)
        
        # Aplicar filtro por nivel si se especificó
        if nivel and nivel.isdigit():
            nivel_int = int(nivel)
            categorias_actual = categorias_actual.filter(nivel=nivel_int)
            # Mantenemos todas las categorías de comparación para poder hacer match
            # pero solo mostraremos las que correspondan al nivel filtrado

        # 4. Preparar datos para comparación
        datos_comparacion = []
        categorias = []
        costos_actual = []
        costos_comparar = []
        niveles = []  # Nuevo campo para almacenar niveles
        
        # Comparar categorías existentes en ambos proyectos
        for cat_actual in categorias_actual:
            cat_comparada = categorias_comparar.filter(
                categoria_relacionada=cat_actual.categoria_relacionada
            ).first()
            
            categorias.append(cat_actual.nombre)
            costos_actual.append(float(cat_actual.total_costo) if cat_actual.total_costo else 0)
            niveles.append(cat_actual.nivel)  # Almacenar nivel de cada categoría
            
            if cat_comparada:
                costos_comparar.append(float(cat_comparada.total_costo) if cat_comparada.total_costo else 0)
            else:
                costos_comparar.append(0)

        # 5. Retornar respuesta estructurada
        response_data = {
            'categorias': categorias,
            'costos_proyecto_actual': costos_actual,
            'costos_proyecto_comparar': costos_comparar,
            'niveles': niveles,  # Nuevo campo con información de niveles
            'nombres': {
                'actual': proyecto_actual.nombre,
                'comparar': proyecto_comparar.nombre
            }
        }
        
        return JsonResponse(response_data)
        
    except ProyectoNuevo.DoesNotExist:
        return JsonResponse({'error': 'Proyecto no encontrado'}, status=404)


def obtener_niveles_proyecto(request, proyecto_id):
    try:
        niveles = CategoriaNuevo.objects.filter(
            proyecto_id=proyecto_id
        ).order_by('nivel').values_list('nivel', flat=True).distinct()
        
        return JsonResponse(list(niveles), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)





def Inicio(request):
    proyectos = ProyectoNuevo.objects.prefetch_related('categorias')
    
    for proyecto in proyectos:
        proyecto.costo_total = proyecto.calcular_costo_total()  # Precalcular el costo total
    
    context = {
        'proyectonuevo': proyectos
    }
    return render(request, 'inicio.html', context)


def cargar_datos(request):
    if request.method == 'POST':
        archivo = request.POST.get('archivo')  # Archivo a cargar seleccionado por el usuario

        if archivo == "proyecto":
            cargar_proyecto_nuevo()
        elif archivo == "categoria":
            cargar_categoria_nueva()
        elif archivo == "costo":
            cargar_costo_nuevo()
        elif archivo == "adquisiciones":
            cargar_adquisiciones()
        elif archivo == "materiales_otros":
            cargar_materiales_otros()
        elif archivo == "mano_obra":
            cargar_mano_obra()
        elif archivo == "equipos_construccion":
            cargar_equipos_construccion()
        elif archivo == "apu_general":
            cargar_apu_general()
        elif archivo == "apu_especifico":
            cargar_apu_especifico()
        elif archivo == "especifico_categoria":
            cargar_especifico_categoria()
        elif archivo == "staff_enami":
            cargar_staff_enami()
        elif archivo == "datos_ep":
            cargar_datos_ep()
        elif archivo == "datos_otros_ep":
            cargar_datos_otros_ep()
        elif archivo == "cantidades":
            cargar_cantidades()
        elif archivo == "contrato_subcontrato":
            cargar_contrato_subcontrato()
        elif archivo == "cotizacion_materiales":
            cargar_cotizacion_materiales()
        elif archivo == "ingenieria_detalles_contraparte":
            cargar_ingenieria_detalles_contraparte()
        elif archivo == "gestion_permisos":
            cargar_gestion_permisos()
        elif archivo == "dueno":
            cargar_dueno()
        elif archivo == "mb":
            cargar_mb()
        elif archivo == "administracion_supervision":
            cargar_administracion_supervision()
        elif archivo == "personal_indirecto_contratista":
            cargar_personal_indirecto_contratista()
        elif archivo == "servicios_apoyo":
            cargar_servicios_apoyo()
        elif archivo == "otros_adm":
            cargar_otros_adm()
        elif archivo == "administrativo_financiero":
            cargar_administrativo_financiero()
        elif archivo == "todos":
            # Si se selecciona "todos", se cargan todos los archivos
            cargar_proyecto_nuevo()
            cargar_categoria_nueva()
            cargar_costo_nuevo()
            cargar_adquisiciones()
            cargar_materiales_otros()
            cargar_mano_obra()
            cargar_equipos_construccion()
            cargar_apu_general()
            cargar_apu_especifico()
            cargar_especifico_categoria()
            cargar_staff_enami()
            cargar_datos_ep()
            cargar_datos_otros_ep()
            cargar_cantidades()
            cargar_contrato_subcontrato()
            cargar_cotizacion_materiales()
            cargar_ingenieria_detalles_contraparte()
            cargar_gestion_permisos()
            cargar_dueno()
            cargar_mb()
            cargar_administracion_supervision()
            cargar_personal_indirecto_contratista()
            cargar_servicios_apoyo()
            cargar_otros_adm()
            cargar_administrativo_financiero()
        else:
            return JsonResponse({'error': 'Archivo no válido'}, status=400)

        return JsonResponse({'mensaje': f'Datos de {archivo} cargados exitosamente'}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)




def listar_archivos(request):
    # Ruta de la carpeta 'uploads' dentro de MEDIA_ROOT
    ruta_uploads = os.path.join(settings.MEDIA_ROOT, 'uploads')

    # Diccionario para almacenar carpetas y sus archivos
    carpetas_y_archivos = {}

    # Verificar si la carpeta 'uploads' existe
    if os.path.exists(ruta_uploads):
        # Recorremos la carpeta 'uploads' y sus subcarpetas
        for root, dirs, files in os.walk(ruta_uploads):
            # Evitar mostrar la carpeta 'uploads' misma, solo sus subcarpetas
            if root != ruta_uploads:
                # Obtenemos la ruta relativa de la carpeta
                carpeta_relativa = os.path.relpath(root, settings.MEDIA_ROOT)
                
                # Lista para almacenar los archivos dentro de cada carpeta
                archivos = [os.path.relpath(os.path.join(root, file), settings.MEDIA_ROOT) for file in files]

                # Almacenamos los archivos por carpeta
                carpetas_y_archivos[carpeta_relativa] = archivos
        
        return render(request, 'listar_archivos.html', {'carpetas_y_archivos': carpetas_y_archivos})
    else:
        return render(request, 'listar_archivos.html', {'error': 'La carpeta "uploads" no existe.'})







class ListadoProyectoNuevo(ListView):
    model = ProyectoNuevo
    template_name = 'tabla_proyecto_nuevo.html'
    context_object_name = 'proyectonuevo'

    def get_queryset(self):
        proyectos = ProyectoNuevo.objects.prefetch_related('categorias')
        
        for proyecto in proyectos:
            proyecto.costo_total = proyecto.calcular_costo_total()  # Precalcular el costo total
        return proyectos
    

    
    
    
class ActualizarProyectoNuevo(UpdateView):
    model = ProyectoNuevo
    form_class = ProyectoNuevoForm
    template_name = 'crear_proyecto_nuevo.html'
    success_url = reverse_lazy('tabla_proyecto_nuevo')

    def get_object(self, queryset=None):
        # Asegúrate de que se está obteniendo el objeto correcto
        return ProyectoNuevo.objects.get(pk=self.kwargs['pk'])

class EliminarProyectoNuevo(DeleteView):
    model = ProyectoNuevo
    template_name = 'proyectonuevo_confirm_delete.html'
    success_url = reverse_lazy('tabla_proyecto_nuevo')

class CrearProyectoNuevo(CreateView):
    model = ProyectoNuevo
    form_class = ProyectoNuevoForm
    template_name = 'crear_proyecto_nuevo.html'
    success_url = reverse_lazy('tabla_proyecto_nuevo')

class ListadoCategoriaNuevo(ListView):
    model = CategoriaNuevo
    template_name = 'tabla_categoria_nuevo.html'
    context_object_name = 'categorianuevo'

    
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values("id", "nombre", "proyecto", "id_padre", "categoria_relacionada","nivel", "final", "total_costo"))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    

class ActualizarCategoriaNuevo(UpdateView):
    model = CategoriaNuevo
    form_class = CategoriaNuevoForm
    template_name = 'crear_categoria_nuevo.html'
    success_url = reverse_lazy('tabla_categoria_nuevo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Categoría'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    

@csrf_exempt
def eliminar_categoria(request):
    if request.method == "POST":
        categoria_id = request.POST.get("id")
        try:
            categoria = CategoriaNuevo.objects.get(id=categoria_id)
            categoria.delete()
            return JsonResponse({"success": True})
        except CategoriaNuevo.DoesNotExist:
            return JsonResponse({"success": False, "error": "Categoría no encontrada"})
    return JsonResponse({"success": False, "error": "Método no permitido"})

class CrearCategoriaNuevo(CreateView):
    model = CategoriaNuevo
    form_class = CategoriaNuevoForm
    template_name = 'crear_categoria_nuevo.html'
    success_url = reverse_lazy('tabla_categoria_nuevo')

class ListadoCostoNuevo(ListView):
    model = CostoNuevo
    template_name = 'tabla_costo_nuevo.html'
    context_object_name = 'costonuevo'

class ActualizarCostoNuevo(UpdateView):
    model = CostoNuevo
    form_class = CostoNuevoForm
    template_name = 'crear_costo_nuevo.html'
    success_url = reverse_lazy('tabla_costo_nuevo')

    def get_object(self, queryset=None):
        # Asegúrate de que se está obteniendo el objeto correcto
        return CostoNuevo.objects.get(pk=self.kwargs['pk'])

class EliminarCostoNuevo(DeleteView):
    model = CostoNuevo
    template_name = 'costonuevo_confirm_delete.html'
    success_url = reverse_lazy('tabla_costo_nuevo')

class CrearCostoNuevo(CreateView):
    model = CostoNuevo
    form_class = CostoNuevoForm
    template_name = 'crear_costo_nuevo.html'
    success_url = reverse_lazy('tabla_costo_nuevo')

class ListadoAdquisiciones(ListView):
    model = Adquisiciones
    template_name = 'tabla_adquisiciones.html'
    context_object_name = 'adquisiciones'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values("id","id_categoria","tipo_origen","tipo_categoria","costo_unitario","crecimiento","flete","total","total_con_flete"))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarAdquisiciones(UpdateView):
    model = Adquisiciones
    form_class = AdquisicionesForm
    template_name = 'editar_adquisiciones.html'
    success_url = reverse_lazy('tabla_adquisiciones')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Adquisicion'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    

@csrf_exempt
def eliminar_adquisicion(request):
    if request.method == "POST":
        adquisicion_id = request.POST.get("id")  # Obtener el ID desde la petición

        try:
            adquisicion = Adquisiciones.objects.get(id=adquisicion_id)
            adquisicion.delete()
            return JsonResponse({"success": True})
        except Adquisiciones.DoesNotExist:
            return JsonResponse({"success": False, "error": "Adquisición no encontrada"})
    
    return JsonResponse({"success": False, "error": "Método no permitido"})

class CrearAdquisiciones(CreateView):
    model = Adquisiciones
    form_class = AdquisicionesForm
    template_name = 'crear_adquisiciones.html'
    success_url = reverse_lazy('tabla_adquisiciones')

class ListadoMaterialesOtros(ListView):
    model = MaterialesOtros
    template_name = 'tabla_materiales_otros.html'
    context_object_name = 'materiales_otros'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values("id", "id_categoria", "costo_unidad", "crecimiento","total_usd","fletes","total_sitio"))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarMaterialesOtros(UpdateView):
    model = MaterialesOtros
    form_class = MaterialesOtrosForm
    template_name = 'crear_materiales_otros.html'
    success_url = reverse_lazy('tabla_materiales_otros')

    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['titulo'] = 'Editar Material'  # Agregar título diferente para edición
            context['accion'] = 'Editar'
            return context



@csrf_exempt  # Para pruebas, pero mejor usa CSRF Token en producción
def eliminar_material(request):
    if request.method == 'POST':
        material_id = request.POST.get('id')
        try:
            material = MaterialesOtros.objects.get(id=material_id)
            material.delete()  # Se ejecuta el método delete()
            return JsonResponse({'success': True})
        except MaterialesOtros.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class CrearMaterialesOtros(CreateView):
    model = MaterialesOtros
    form_class = MaterialesOtrosForm
    template_name = 'crear_materiales_otros.html'
    success_url = reverse_lazy('tabla_materiales_otros')

class ListadoCantidades(ListView):
    model = Cantidades
    template_name = "tabla_cantidades.html"
    context_object_name = "cantidades"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values("id", "id_categoria", "unidad_medida", "cantidad", "fc", "cantidad_final"))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarCantidades(UpdateView):
    model = Cantidades
    form_class = CantidadesForm
    template_name = 'crear_cantidades.html'
    success_url = reverse_lazy('tabla_cantidades')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Cantidad'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

class CrearCantidades(CreateView):
    model = Cantidades
    form_class = CantidadesForm
    template_name = 'crear_cantidades.html'
    success_url = reverse_lazy('tabla_cantidades')
    
@csrf_exempt
def eliminar_cantidad(request):
    if request.method == 'POST':
        cantidad_id = request.POST.get('id')
        try:
            cantidad = Cantidades.objects.get(id=cantidad_id)
            cantidad.delete()
            return JsonResponse({'success': True})
        except Cantidades.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cantidad no encontrada'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})



class ListadoEquiposConstruccion(ListView):
    model = EquiposConstruccion
    template_name = 'tabla_equipos_construccion.html'
    context_object_name = 'equipos_construccion'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values("id", "id_categoria", "horas_maquina_unidad", "costo_maquina_hora", "total_horas_maquina", "total_usd"))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    

class ActualizarEquiposConstruccion(UpdateView):
    model = EquiposConstruccion
    form_class = EquiposConstruccionForm
    template_name = 'crear_equipos_construccion.html'
    success_url = reverse_lazy('tabla_equipos_construccion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Equipos Construccion'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context


@csrf_exempt
def eliminar_equipo_construccion(request):
    if request.method == "POST":
        equipo_id = request.POST.get("id")  # Obtener el ID desde la petición

        try:
            equipo = EquiposConstruccion.objects.get(id=equipo_id)
            equipo.delete()
            return JsonResponse({"success": True})
        except EquiposConstruccion.DoesNotExist:
            return JsonResponse({"success": False, "error": "Equipo de construcción no encontrado"})
    
    return JsonResponse({"success": False, "error": "Método no permitido"})

class CrearEquiposConstruccion(CreateView):
    model = EquiposConstruccion
    form_class = EquiposConstruccionForm
    template_name = 'crear_equipos_construccion.html'
    success_url = reverse_lazy('tabla_equipos_construccion')

class ListadoManoObra(ListView):
    model = ManoObra
    template_name = 'tabla_mano_obra.html'
    context_object_name = 'mano_obra'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values(
                "id",
                "id_categoria",  # ✅ Devuelve el nombre en lugar del ID
                "horas_hombre_unidad",
                "fp",
                "rendimiento",  # ✅ Nuevo campo
                "horas_hombre_final",
                "cantidad_horas_hombre",
                "costo_hombre_hora",
                "tarifas_usd_hh_mod",  # ✅ Nuevo campo
                "total_hh",
                "total_usd_mod",
                "tarifa_usd_hh_equipos",
                "total_usd_equipos",
                "total_usd",  # ✅ Nuevo cálculo agregado
                
                
            ))
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarManoObra(UpdateView):
    model = ManoObra
    form_class = ManoObraForm
    template_name = 'crear_mano_obra.html'
    success_url = reverse_lazy('tabla_mano_obra')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Equipos Construccion'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    

@csrf_exempt
def eliminar_mano_obra(request):
    if request.method == "POST":
        mano_obra_id = request.POST.get("id")  # Obtener el ID desde la petición

        try:
            mano_obra = ManoObra.objects.get(id=mano_obra_id)
            mano_obra.delete()
            return JsonResponse({"success": True})
        except ManoObra.DoesNotExist:
            return JsonResponse({"success": False, "error": "Registro de mano de obra no encontrado"})
    
    return JsonResponse({"success": False, "error": "Método no permitido"})

class CrearManoObra(CreateView):
    model = ManoObra
    form_class = ManoObraForm
    template_name = 'crear_mano_obra.html'
    success_url = reverse_lazy('tabla_mano_obra')

class ListadoAPUGeneral(ListView):
    model = ApuGeneral
    template_name = 'tabla_apu_general.html'
    context_object_name = 'apu_general'

class ActualizarAPUGeneral(UpdateView):
    model = ApuGeneral
    form_class = APUGeneralForm
    template_name = 'crear_apu_general.html'
    success_url = reverse_lazy('tabla_apu_general')

    def get_object(self, queryset=None):
        # Asegúrate de que se está obteniendo el objeto correct
        return ApuGeneral.objects.get(pk=self.kwargs['pk'])

class EliminarAPUGeneral(DeleteView):
    model = ApuGeneral
    template_name = 'apu_general_confirm_delete.html'
    success_url = reverse_lazy('tabla_apu_general')

class CrearAPUGeneral(CreateView):
    model = ApuGeneral
    form_class = APUGeneralForm
    template_name = 'crear_apu_general.html'
    success_url = reverse_lazy('tabla_apu_general')

class ListadoAPUEspecifico(ListView):
    model = ApuEspecifico
    template_name = 'tabla_apu_especifico.html'
    context_object_name = 'apu_especifico'

class ActualizarAPUEspecifico(UpdateView):
    model = ApuEspecifico
    form_class = APUEspecificoForm
    template_name = 'crear_apu_especifico.html'
    success_url = reverse_lazy('tabla_apu_especifico')

    def get_object(self, queryset=None):
        # Asegúrate de que se está obteniendo el objeto correct
        return ApuEspecifico.objects.get(pk=self.kwargs['pk'])
    
class EliminarAPUEspecifico(DeleteView):
    model = ApuEspecifico
    template_name = 'apu_especifico_confirm_delete.html'
    success_url = reverse_lazy('tabla_apu_especifico')

class CrearAPUEspecifico(CreateView):
    model = ApuEspecifico
    form_class = APUEspecificoForm
    template_name = 'crear_apu_especifico.html'
    success_url = reverse_lazy('tabla_apu_especifico')

class ListadoEspecificoCategoria(ListView):
    model = EspecificoCategoria
    template_name = 'tabla_especifico_categoria.html'
    context_object_name = 'especifico_categoria'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'unidad', 'cantidad', 'dedicacion', 'duracion', 'costo', 'total'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarEspecificoCategoria(UpdateView):
    model = EspecificoCategoria
    form_class = EspecificoCategoriaForm
    template_name = 'crear_especifico_categoria.html'
    success_url = reverse_lazy('tabla_especifico_categoria')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar GG Constructor'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class EliminarEspecificoCategoria(DeleteView):
    model = EspecificoCategoria
    template_name = 'especifico_categoria_confirm_delete.html'
    success_url = reverse_lazy('tabla_especifico_categoria')

@csrf_exempt  # Para pruebas, pero mejor usa CSRF Token en producción
def eliminar_especifico_categoria(request):
    if request.method == 'POST':
        especifico_id = request.POST.get('id')  # Obtener el ID desde la petición
        try:
            especifico = EspecificoCategoria.objects.get(id=especifico_id)
            especifico.delete()  # Se ejecuta el método delete()
            return JsonResponse({'success': True})
        except EspecificoCategoria.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}) 

class CrearEspecificoCategoria(CreateView):
    model = EspecificoCategoria
    form_class = EspecificoCategoriaForm
    template_name = 'crear_especifico_categoria.html'
    success_url = reverse_lazy('tabla_especifico_categoria')

class ListadoStaffEnami(ListView):
    model = StaffEnami
    template_name = 'tabla_staff_enami.html'
    context_object_name = 'staff_enami'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'nombre', 'valor', 'dotacion', 'duracion', 'factor_utilizacion', 'total_horas_hombre', 'costo_total','categoria'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarStaffEnami(UpdateView):
    model = StaffEnami
    form_class = StaffEnamiForm
    template_name = 'crear_staff_enami.html'
    success_url = reverse_lazy('tabla_staff_enami')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Staff Enami'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

class EliminarStaffEnami(DeleteView):
    model = StaffEnami
    template_name = 'staff_enami_confirm_delete.html'
    success_url = reverse_lazy('tabla_staff_enami')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_staff_enami(request):
    if request.method == 'POST':
        staff_id = request.POST.get('id')
        try:
            staff = StaffEnami.objects.get(id=staff_id)
            staff.delete()
            return JsonResponse({'success': True})
        except StaffEnami.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


class CrearStaffEnami(CreateView):
    model = StaffEnami
    form_class = StaffEnamiForm
    template_name = 'crear_staff_enami.html'
    success_url = reverse_lazy('tabla_staff_enami')

class ListadoDatosOtrosEP(ListView):
    model = DatosOtrosEP
    template_name = 'tabla_datos_otros_ep.html'
    context_object_name = 'datos_otros_ep'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'comprador', 'dedicacion', 'plazo','sueldo_pax','gestiones','viajes','id_categoria'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarDatosOtrosEP(UpdateView):
    model = DatosOtrosEP
    form_class = DatosOtrosEPForm
    template_name = 'crear_datos_otros_ep.html'
    success_url = reverse_lazy('tabla_datos_otros_ep')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Datos Otros EP'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

@csrf_exempt  # Para desarrollo, en producción usa CSRF token adecuadamente
def eliminar_datos_otros_ep(request):
    if request.method == 'POST':
        datos_id = request.POST.get('id')
        try:
            datos = DatosOtrosEP.objects.get(id=datos_id)
            
            # Guardamos referencia a la categoría antes de eliminar
            categoria = datos.id_categoria
            categoria_padre = categoria.id_padre if categoria else None
            
            # Eliminamos el registro
            datos.delete()
            
            # Actualizamos costos en la jerarquía
            if categoria:
                categoria.actualizar_total_costo()
            
            # Actualizamos categorías padres
            while categoria_padre:
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre
            
            return JsonResponse({'success': True, 'message': 'Registro eliminado correctamente'})
            
        except DatosOtrosEP.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

class CrearDatosOtrosEP(CreateView):
    model = DatosOtrosEP
    form_class = DatosOtrosEPForm
    template_name = 'crear_datos_otros_ep.html'
    success_url = reverse_lazy('tabla_datos_otros_ep')

class ListadoDatosEP(ListView):
    model = DatosEP
    template_name = 'tabla_datos_ep.html'
    context_object_name = 'datos_ep'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'hh_profesionales', 'precio_hh', 'id_categoria'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)

class ActualizarDatosEP(UpdateView):
    model = DatosEP
    form_class = DatosEPForm
    template_name = 'crear_datos_ep.html'
    success_url = reverse_lazy('tabla_datos_ep')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Datos EP'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

@csrf_exempt  # Solo para desarrollo, en producción usa CSRF token adecuadamente
def eliminar_datos_ep(request):
    if request.method == 'POST':
        datos_ep_id = request.POST.get('id')
        try:
            datos_ep = DatosEP.objects.get(id=datos_ep_id)
            
            # Guardamos referencia a la categoría antes de eliminar
            categoria = datos_ep.id_categoria
            categoria_padre = categoria.id_padre if categoria else None
            
            # Eliminamos el registro
            datos_ep.delete()
            
            # Actualizamos costos
            if categoria:
                categoria.actualizar_total_costo()
            
            # Actualizamos categorías padres
            while categoria_padre:
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre
            
            return JsonResponse({'success': True})
            
        except DatosEP.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


class CrearDatosEP(CreateView):
    model = DatosEP
    form_class = DatosEPForm
    template_name = 'crear_datos_ep.html'
    success_url = reverse_lazy('tabla_datos_ep')

class ListadoCotizacionMateriales(ListView):
    model = CotizacionMateriales
    template_name = 'tabla_cotizacion_materiales.html'
    context_object_name = 'cotizacion_materiales'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'tipo_suministro', 'tipo_moneda', 'pais_entrega', 'fecha_cotizacion_referencia', 'cotizacion_usd', 'cotizacion_clp','factor_correccion','moneda_aplicada','flete_unitario','origen_precio','cotizacion','moneda_origen','tasa_cambio'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarCotizacionMateriales(UpdateView):
    model = CotizacionMateriales
    form_class = CotizacionMaterialesForm
    template_name = 'crear_cotizacion_materiales.html'
    success_url = reverse_lazy('tabla_cotizacion_materiales')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Cotización Materiales'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

class CrearCotizacionMateriales(CreateView):
    model = CotizacionMateriales
    form_class = CotizacionMaterialesForm
    template_name = 'crear_cotizacion_materiales.html'
    success_url = reverse_lazy('tabla_cotizacion_materiales')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_cotizacion_materiales(request):
    if request.method == 'POST':
        cotizacion_materiales_id = request.POST.get('id')
        try:
            cotizacion_materiales = CotizacionMateriales.objects.get(id=cotizacion_materiales_id)
            cotizacion_materiales.delete()
            return JsonResponse({'success': True})
        except CotizacionMateriales.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoContratoSubcontrato(ListView):
    model = ContratoSubcontrato
    template_name = 'tabla_contrato_subcontrato.html'
    context_object_name = 'contrato_subcontrato'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'costo_laboral_indirecto_usd_hh', 'total_usd_indirectos_contratista', 'usd_por_unidad', 'fc_subcontrato', 'usd_total_subcontrato', 'costo_contrato_total','costo_contrato_unitario'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarContratoSubcontrato(UpdateView):
    model = ContratoSubcontrato
    form_class = ContratoSubcontratoForm
    template_name = 'crear_contrato_subcontrato.html'
    success_url = reverse_lazy('tabla_contrato_subcontrato')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Contrato Subcontrato'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

class CrearContratoSubcontrato(CreateView):
    model = ContratoSubcontrato
    form_class = ContratoSubcontratoForm
    template_name = 'crear_contrato_subcontrato.html'
    success_url = reverse_lazy('tabla_contrato_subcontrato')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_contrato_subcontrato(request):
    if request.method == 'POST':
        contrato_subcontrato_id = request.POST.get('id')
        try:
            contrato_subcontrato = ContratoSubcontrato.objects.get(id=contrato_subcontrato_id)
            contrato_subcontrato.delete()
            return JsonResponse({'success': True})
        except ContratoSubcontrato.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


class ListadoIngenieriaDetallesContraparte(ListView):
    model = IngenieriaDetallesContraparte
    template_name = 'tabla_ingenieria_detalles_contraparte.html'
    context_object_name = 'ingenieria_detalles_contraparte'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'nombre', 'UF', 'MB','total_usd'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarIngenieriaDetallesContraparte(UpdateView):
    model = IngenieriaDetallesContraparte
    form_class = IngenieriaDetallesContraparteForm
    template_name = 'crear_ingenieria_detalles_contraparte.html'
    success_url = reverse_lazy('tabla_ingenieria_detalles_contraparte')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Ingenieria Detalles Contraparte'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearIngenieriaDetallesContraparte(CreateView):
    model = IngenieriaDetallesContraparte
    form_class = IngenieriaDetallesContraparteForm
    template_name = 'crear_ingenieria_detalles_contraparte.html'
    success_url = reverse_lazy('tabla_ingenieria_detalles_contraparte')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_ingenieria_detalles_contraparte(request):
    if request.method == 'POST':
        ingenieria_id = request.POST.get('id')
        try:
            ingenieria = IngenieriaDetallesContraparte.objects.get(id=ingenieria_id)
            ingenieria.delete()
            return JsonResponse({'success': True})
        except IngenieriaDetallesContraparte.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoGestionPermisos(ListView):
    model = GestionPermisos
    template_name = 'tabla_gestion_permisos.html'
    context_object_name = 'gestion_permisos'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'nombre', 'dedicacion', 'meses','cantidad','turno','MB','HH','total_usd'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarGestionPermisos(UpdateView):
    model = GestionPermisos
    form_class = GestionPermisosForm
    template_name = 'crear_gestion_permisos.html'
    success_url = reverse_lazy('tabla_gestion_permisos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Gestión de Permisos'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearGestionPermisos(CreateView):
    model = GestionPermisos
    form_class = GestionPermisosForm
    template_name = 'crear_gestion_permisos.html'
    success_url = reverse_lazy('tabla_gestion_permisos') 

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_gestion_permisos(request):
    if request.method == 'POST':
        permiso_id = request.POST.get('id')
        try:
            permiso = GestionPermisos.objects.get(id=permiso_id)
            permiso.delete()
            return JsonResponse({'success': True})
        except GestionPermisos.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoDueno(ListView):
    model = Dueno
    template_name = 'tabla_dueno.html'
    context_object_name = 'dueno'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'nombre', 'total_hh', 'costo_hh_us','costo_total'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarDueno(UpdateView):
    model = Dueno
    form_class = DuenoForm
    template_name = 'crear_dueno.html'
    success_url = reverse_lazy('tabla_dueno')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Dueño'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context

class CrearDueno(CreateView):
    model = Dueno
    form_class = DuenoForm
    template_name = 'crear_dueno.html'
    success_url = reverse_lazy('tabla_dueno')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_dueno(request):
    if request.method == 'POST':
        dueno_id = request.POST.get('id')
        try:
            dueno = Dueno.objects.get(id=dueno_id)
            dueno.delete()
            return JsonResponse({'success': True})
        except Dueno.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoMB(ListView):
    model = MB
    template_name = "tabla_mb.html"
    context_object_name = "mb"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'mb', 'fc', 'anio'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarMB(UpdateView):
    model = MB
    form_class = MBForm
    template_name = 'crear_mb.html'
    success_url = reverse_lazy('tabla_mb')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar MB'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearMB(CreateView):
    model = MB
    form_class = MBForm
    template_name = 'crear_mb.html'
    success_url = reverse_lazy('tabla_mb')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_mb(request):
    if request.method == 'POST':
        mb_id = request.POST.get('id')  # Obtener el ID del MB a eliminar
        try:
            mb = MB.objects.get(id=mb_id)
            mb.delete()  # Eliminar el registro
            return JsonResponse({'success': True})
        except MB.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoAdministracionSupervision(ListView):
    model = AdministracionSupervision
    template_name = "tabla_administracion_supervision.html"
    context_object_name = "administracion_supervision"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'unidad', 'precio_unitario_clp', 'total_unitario','factor_uso','cantidad_u_persona','mb_seleccionado','costo_total_clp','costo_total_us','costo_total_mb'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarAdministracionSupervision(UpdateView):
    model = AdministracionSupervision
    form_class = AdministracionSupervisionForm 
    template_name = 'crear_administracion_supervision.html'
    success_url = reverse_lazy('tabla_administracion_supervision')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Administración y Supervisión'
        context['accion'] = 'Editar'
        return context

    
class CrearAdministracionSupervision(CreateView):
    model = AdministracionSupervision
    form_class = AdministracionSupervisionForm
    template_name = 'crear_administracion_supervision.html'
    success_url = reverse_lazy('tabla_administracion_supervision')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_administracion_supervision(request):
    if request.method == 'POST':
        # Obtener el ID del objeto a eliminar
        admin_sup_id = request.POST.get('id')
        try:
            # Buscar el objeto por ID
            admin_sup = AdministracionSupervision.objects.get(id=admin_sup_id)
            # Eliminar el objeto
            admin_sup.delete()
            return JsonResponse({'success': True})
        except AdministracionSupervision.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoPersonalIndirectoContratista(ListView):
    model = PersonalIndirectoContratista
    template_name = "tabla_personal_indirecto_contratista.html"
    context_object_name = "personal_indirecto_contratista"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'mb_seleccionado', 'turno', 'unidad','hh_mes','plazo_mes','total_hh','precio_unitario_clp_hh','tarifa_usd_hh','costo_total_clp','costo_total_us','costo_total_mb'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarPersonalIndirectoContratista(UpdateView):
    model = PersonalIndirectoContratista
    form_class = PersonalIndirectoContratistaForm
    template_name = 'crear_personal_indirecto_contratista.html'
    success_url = reverse_lazy('tabla_personal_indirecto_contratista')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Personal Indirecto Contratista'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearPersonalIndirectoContratista(CreateView):
    model = PersonalIndirectoContratista
    form_class = PersonalIndirectoContratistaForm
    template_name = 'crear_personal_indirecto_contratista.html'
    success_url = reverse_lazy('tabla_personal_indirecto_contratista')

@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_personal_indirecto_contratista(request):
    if request.method == 'POST':
        # Obtener el ID del objeto a eliminar
        personal_id = request.POST.get('id')
        try:
            # Buscar el objeto por ID
            personal = PersonalIndirectoContratista.objects.get(id=personal_id)
            
            # Guardar la categoría padre antes de eliminar
            categoria_padre = personal.id_categoria.id_padre if personal.id_categoria else None
            
            # Eliminar el objeto
            personal.delete()
            
            # Actualizar la categoría y sus categorías superiores
            if personal.id_categoria:
                personal.id_categoria.actualizar_total_costo()
            
            while categoria_padre:
                print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

            return JsonResponse({'success': True})
        except PersonalIndirectoContratista.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoServiciosApoyo(ListView):
    model = ServiciosApoyo
    template_name = "tabla_servicios_apoyo.html"
    context_object_name = "servicios_apoyo"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'unidad', 'cantidad', 'hh_totales','tarifas_clp','mb','total_usd'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarServiciosApoyo(UpdateView):
    model = ServiciosApoyo
    form_class = ServiciosApoyoForm
    template_name = 'crear_servicios_apoyo.html'
    success_url = reverse_lazy('tabla_servicios_apoyo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Servicios de Apoyo'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearServiciosApoyo(CreateView):
    model = ServiciosApoyo
    form_class = ServiciosApoyoForm
    template_name = 'crear_servicios_apoyo.html'
    success_url = reverse_lazy('tabla_servicios_apoyo')
    
@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_servicios_apoyo(request):
    if request.method == 'POST':
        # Obtener el ID del objeto a eliminar
        servicio_apoyo_id = request.POST.get('id')
        try:
            # Buscar el objeto por ID
            servicio_apoyo = ServiciosApoyo.objects.get(id=servicio_apoyo_id)
            # Eliminar el objeto
            servicio_apoyo.delete()
            return JsonResponse({'success': True})
        except ServiciosApoyo.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

class ListadoOtrosADM(ListView):
    model = OtrosADM
    template_name = "tabla_otros_adm.html"
    context_object_name = "otros_adm"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'HH', 'MB', 'total_usd','dedicacion','meses','cantidad','turno'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarOtrosADM(UpdateView):
    model = OtrosADM
    form_class = OtrosADMForm
    template_name = 'crear_otros_adm.html'
    success_url = reverse_lazy('tabla_otros_adm')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Otros ADM'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearOtrosADM(CreateView):
    model = OtrosADM
    form_class = OtrosADMForm
    template_name = 'crear_otros_adm.html'
    success_url = reverse_lazy('tabla_otros_adm')
    
@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_otros_adm(request):
    if request.method == 'POST':
        # Obtener el ID del objeto a eliminar
        otros_adm_id = request.POST.get('id')
        try:
            # Buscar el objeto por ID
            otros_adm = OtrosADM.objects.get(id=otros_adm_id)
            # Eliminar el objeto
            otros_adm.delete()  # Se llamará al método delete del modelo
            return JsonResponse({'success': True})
        except OtrosADM.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


class ListadoAdministrativoFinanciero(ListView):
    model = AdministrativoFinanciero
    template_name = "tabla_administrativo_financiero.html"
    context_object_name = "administrativo_financiero"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  
            data = list(self.get_queryset().values('id', 'id_categoria', 'unidad', 'valor', 'meses','sobre_contrato_base','costo_total'))  # ✅ Convertimos a lista de diccionarios
            return JsonResponse(data, safe=False)  

        return super().get(request, *args, **kwargs)
    
class ActualizarAdministrativoFinanciero(UpdateView):
    model = AdministrativoFinanciero
    form_class = AdministrativoFinancieroForm
    template_name = 'crear_administrativo_financiero.html'
    success_url = reverse_lazy('tabla_administrativo_financiero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Administrativo Financiero'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
class CrearAdministrativoFinanciero(CreateView):
    model = AdministrativoFinanciero
    form_class = AdministrativoFinancieroForm
    template_name = 'crear_administrativo_financiero.html'
    success_url = reverse_lazy('tabla_administrativo_financiero')
    
@csrf_exempt  # Solo para pruebas, usa CSRF Token en producción
def eliminar_administrativo_financiero(request):
    if request.method == 'POST':
        # Obtener el ID del objeto a eliminar
        administrativo_id = request.POST.get('id')
        try:
            # Buscar el objeto por ID
            administrativo = AdministrativoFinanciero.objects.get(id=administrativo_id)
            # Eliminar el objeto
            administrativo.delete()
            return JsonResponse({'success': True})
        except AdministrativoFinanciero.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

    



###############SUMA CATEGORIAS Y SUBCATEGORIAS#####################

def detalle_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoNuevo, id=proyecto_id)
    categorias = CategoriaNuevo.objects.filter(proyecto=proyecto, id_padre__isnull=True)  # Solo las categorías raíz

    return render(request, 'desplegable.html', {'proyecto': proyecto, 'categorias': categorias})


def obtener_subcategorias(request, categoria_id):
    """Devuelve las subcategorías de una categoría en formato JSON."""
    subcategorias = CategoriaNuevo.objects.filter(id_padre_id=categoria_id).values('id', 'nombre', 'total_costo')

    return JsonResponse(list(subcategorias), safe=False)



####ACA OBTENER SUBCATEGORIAS PARA DESPLEGABLE##########

@api_view(['GET'])
def obtener_subcategorias(request, categoria_id):
    try:
        categoria = CategoriaNuevo.objects.get(id=categoria_id)
    except CategoriaNuevo.DoesNotExist:
        return Response({"error": "Categoría no encontrada"}, status=404)

    # Obtener subcategorías de primer nivel
    subcategorias = categoria.subcategorias.all()

    # Función recursiva para obtener todos los niveles de subcategorías
    def get_all_subcategorias(categoria):
        subcategoria_data = []
        for subcategoria in categoria.subcategorias.all():
            sub_subcategorias = get_all_subcategorias(subcategoria)  # Recursión para obtener sub-subcategorías
            subcategoria_data.append({
                'id': subcategoria.id,
                'nombre': subcategoria.nombre,
                'costo': subcategoria.total_costo,
                'sub_subcategorias': sub_subcategorias
            })
        return subcategoria_data

    # Obtener todas las subcategorías para la categoría
    subcategoria_data = get_all_subcategorias(categoria)

    return Response(subcategoria_data)






###################ACA RELACIONADO A SUBIR ARCHIVOS DESDE TEMPLATE#######################################
def subir_archivo(request):
    if request.method == 'POST':
        form = ArchivoSubidoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.save(commit=False)  # No guardar inmediatamente, queremos moverlo primero
            
            # Obtener el nombre del archivo y la carpeta destino
            modelo_destino = archivo.modelo_destino
            destino_dir = os.path.join(settings.BASE_DIR, 'uploads', modelo_destino)
            
            # Crear la carpeta de destino si no existe
            os.makedirs(destino_dir, exist_ok=True)
            
            # Obtener el nombre del archivo (sin incluir subcarpetas adicionales)
            archivo_nombre = os.path.basename(archivo.archivo.name)
            destino_path = os.path.join(destino_dir, archivo_nombre)
            
            # Guardar el archivo en la carpeta correcta
            with open(destino_path, 'wb+') as destination:
                for chunk in archivo.archivo.chunks():
                    destination.write(chunk)
            
            # Ahora guardamos el modelo con la nueva ubicación del archivo
            archivo.archivo.name = os.path.join(modelo_destino, archivo_nombre)
            archivo.save()  # Guardar el modelo con la ruta actualizada

            # Guardamos el nombre del archivo en la sesión para usarlo después
            request.session['archivo_subido'] = archivo_nombre

            # Redirigir con un contexto que indique que los archivos fueron subidos
            return render(request, 'subir_archivo.html', {'form': form, 'archivos_subidos': True})
    else:
        form = ArchivoSubidoForm()

    return render(request, 'subir_archivo.html', {'form': form})


####################################################################################################################

def categorias_raiz_json(request, proyecto_id):
    categorias = CategoriaNuevo.objects.filter(id_padre__isnull=True, proyecto_id=proyecto_id).values('nombre', 'total_costo')
    data = [{'name': c['nombre'], 'value': float(c['total_costo'])} for c in categorias]
    return JsonResponse(data, safe=False)

def listar_proyectos(request):
    proyectos = ProyectoNuevo.objects.values('id', 'nombre')
    return JsonResponse(list(proyectos), safe=False)

#####################################################################################################################

def exportar_excel(request, modelo_nombre):
    try:
        # Obtener el modelo dinámicamente
        Modelo = apps.get_model(app_label='proyectoApp', model_name=modelo_nombre)
        
        # Obtener los datos de la tabla
        data = Modelo.objects.all().values()
        
        # Convertir datos a un DataFrame de Pandas
        df = pd.DataFrame(list(data))
        
        # Crear la respuesta HTTP con el archivo Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={modelo_nombre}.xlsx'
        
        # Guardar el DataFrame en la respuesta
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Datos')
        
        return response
    except Exception as e:
        return HttpResponse(f"Error al exportar: {str(e)}", status=500)




#########################################################################################################################


def duplicar_proyecto(request, proyecto_id):
    try:
        # 1. Configuración de modelos y campos permitidos
        MODELOS = [
            'ProyectoNuevo',
            'CategoriaNuevo',
            'CostoNuevo',
            'Adquisiciones',
            'MaterialesOtros',
            'ManoObra',
            'EquiposConstruccion',
            'ApuGeneral',
            'ApuEspecifico',
            'EspecificoCategoria',
            'StaffEnami',
            'DatosEP',
            'DatosOtrosEP',
            'Cantidades',
            'ContratoSubcontrato',
            'CotizacionMateriales',
            'IngenieriaDetallesContraparte',
            'GestionPermisos',
            'Dueno',
            'MB',
            'AdministracionSupervision',
            'PersonalIndirectoContratista',
            'ServiciosApoyo',
            'OtrosADM',
            'AdministrativoFinanciero',
        ]

        CAMPOS_PERMITIDOS = {
            'ProyectoNuevo': ['id', 'nombre', 'proyecto_relacionado'],
            'CategoriaNuevo': ['id', 'nombre', 'proyecto', 'id_padre', 'categoria_relacionada', 'final', 'nivel'],
            'CostoNuevo': ['id', 'monto', 'categoria'],
            'Adquisiciones': ['id_categoria', 'tipo_origen', 'tipo_categoria', 'costo_unitario', 'crecimiento'],
            'MaterialesOtros': ['id_categoria', 'costo_unidad', 'crecimiento'],
            'ManoObra': ['id_categoria', 'horas_hombre_unidad', 'fp', 'costo_hombre_hora', 'rendimiento', 'tarifas_usd_hh_mod', 'tarifa_usd_hh_equipos'],
            'EquiposConstruccion': ['id_categoria', 'horas_maquina_unidad', 'costo_maquina_hora'],
            'ApuGeneral': ['id', 'nombre'],
            'ApuEspecifico': ['id_apu_general', 'id_mano_obra', 'nombre', 'unidad_medida', 'cantidad', 'precio_unitario', 'id_categoria'],
            'EspecificoCategoria': ['id_categoria', 'unidad', 'cantidad', 'dedicacion', 'duracion', 'costo'],
            'StaffEnami': ['categoria', 'nombre', 'valor', 'dotacion', 'duracion', 'factor_utilizacion'],
            'DatosEP': ['id', 'hh_profesionales', 'precio_hh', 'id_categoria'],
            'DatosOtrosEP': ['comprador', 'dedicacion', 'plazo', 'sueldo_pax', 'viajes', 'id_categoria'],
            'Cantidades': ['id_categoria', 'unidad_medida', 'cantidad', 'fc'],
            'ContratoSubcontrato': ['id_categoria', 'costo_laboral_indirecto_usd_hh', 'fc_subcontrato'],
            'CotizacionMateriales': ['id_categoria', 'tipo_suministro', 'tipo_moneda', 'pais_entrega', 
                                   'fecha_cotizacion_referencia', 'cotizacion_usd', 'cotizacion_clp', 
                                   'factor_correccion', 'moneda_aplicada', 'origen_precio', 'cotizacion', 
                                   'moneda_origen', 'tasa_cambio', 'flete_unitario'],
            'IngenieriaDetallesContraparte': ['id_categoria', 'nombre', 'UF', 'MB'],
            'GestionPermisos': ['id_categoria', 'nombre', 'dedicacion', 'meses', 'cantidad', 'turno', 'MB'],
            'Dueno': ['id_categoria', 'nombre', 'total_hh', 'costo_hh_us'],
            'MB': ['id', 'mb', 'fc', 'anio'],
            'AdministracionSupervision': ['id_categoria', 'unidad', 'precio_unitario_clp', 'total_unitario', 'factor_uso', 'cantidad_u_persona', 'mb_seleccionado'],
            'PersonalIndirectoContratista': ['id_categoria', 'unidad', 'hh_mes', 'plazo_mes', 'precio_unitario_clp_hh', 'mb_seleccionado', 'turno'],
            'ServiciosApoyo': ['id_categoria', 'unidad', 'cantidad', 'hh_totales', 'tarifas_clp', 'mb'],
            'OtrosADM': ['id_categoria', 'dedicacion', 'meses', 'cantidad', 'turno', 'MB'],
            'AdministrativoFinanciero': ['id_categoria', 'unidad', 'valor', 'meses', 'sobre_contrato_base', 'costo_total'],
        }

        # 2. Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f"duplicado_{proyecto_id}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Diccionario para mapear todos los IDs
                id_mapping = {
                    'ProyectoNuevo': {},
                    'CategoriaNuevo': {},
                    # Agregar otros modelos si necesitas mapear sus IDs
                }

                # 3. Procesar ProyectoNuevo
                Proyecto = apps.get_model('proyectoApp', 'ProyectoNuevo')
                proyecto = Proyecto.objects.get(id=proyecto_id)
                id_mapping['ProyectoNuevo'][proyecto.id] = f"c{proyecto.id}"
                
                data_proyecto = [{
                    'id': id_mapping['ProyectoNuevo'][proyecto.id],
                    'nombre': f"Copia de {proyecto.nombre}",
                    'proyecto_relacionado': proyecto.proyecto_relacionado
                }]
                
                df_proyecto = pd.DataFrame(data_proyecto)
                excel_path = os.path.join(temp_dir, "ProyectoNuevo.xlsx")
                df_proyecto.to_excel(excel_path, index=False)
                zip_file.write(excel_path, "ProyectoNuevo.xlsx")
                
                # 4. Procesar CategoriaNuevo
                Categoria = apps.get_model('proyectoApp', 'CategoriaNuevo')
                categorias = Categoria.objects.filter(proyecto_id=proyecto_id)
                
                data_categorias = []
                for cat in categorias:
                    new_id = f"c{cat.id}"
                    id_mapping['CategoriaNuevo'][cat.id] = new_id
                    
                    item = {
                        'id': new_id,
                        'nombre': cat.nombre,
                        'proyecto': id_mapping['ProyectoNuevo'][proyecto.id],
                        'id_padre': f"c{cat.id_padre}" if cat.id_padre else None,
                        'categoria_relacionada': cat.categoria_relacionada,
                        'nivel': cat.nivel,
                        'final': cat.final,
                        
                    }
                    data_categorias.append(item)
                
                if data_categorias:
                    df_categorias = pd.DataFrame(data_categorias)
                    excel_path = os.path.join(temp_dir, "CategoriaNuevo.xlsx")
                    df_categorias.to_excel(excel_path, index=False)
                    zip_file.write(excel_path, "CategoriaNuevo.xlsx")
                
                # 5. Procesar otros modelos
                for model_name in MODELOS[2:]:  # Saltar los primeros dos
                    try:
                        Model = apps.get_model('proyectoApp', model_name)
                        campos = CAMPOS_PERMITIDOS.get(model_name, [])
                        
                        # Obtener todos los campos que son relaciones
                        relation_fields = [
                            f.name for f in Model._meta.get_fields() 
                            if (f.is_relation and f.many_to_one) or 
                               (f.name.endswith('_id') and f.name != 'id')
                        ]
                        
                        # Filtrar por relaciones con categorías
                        categoria_fields = [f for f in relation_fields 
                                          if f in ['id_categoria', 'categoria'] or 
                                             (f.endswith('_id') and 'categoria' in f.lower())]
                        
                        queryset = Model.objects.filter(**{f"{categoria_fields[0]}__in": list(id_mapping['CategoriaNuevo'].keys())})
                        
                        data = []
                        for obj in queryset:
                            item = {'id': f"c{obj.id}"}
                            
                            for field_name in campos:
                                if field_name == 'id':
                                    continue
                                    
                                try:
                                    value = getattr(obj, field_name)
                                    
                                    # Aplicar prefijo 'c' a:
                                    # 1. Campos que terminan en '_id'
                                    # 2. Campos de relación (ForeignKey)
                                    if field_name.endswith('_id') or field_name in relation_fields:
                                        if value:
                                            item[field_name] = f"c{value}"
                                        else:
                                            item[field_name] = None
                                    else:
                                        item[field_name] = value
                                except AttributeError:
                                    continue
                            
                            data.append(item)
                        
                        if data:
                            df = pd.DataFrame(data)
                            # Ordenar columnas según configuración
                            ordered_columns = [col for col in campos if col in df.columns]
                            df = df[ordered_columns]
                            
                            excel_path = os.path.join(temp_dir, f"{model_name}.xlsx")
                            df.to_excel(excel_path, index=False)
                            zip_file.write(excel_path, f"{model_name}.xlsx")
                    
                    except Exception as e:
                        print(f"Error en {model_name}: {str(e)}")
                        continue

            # 6. Leer y enviar ZIP
            with open(zip_path, 'rb') as f:
                zip_data = f.read()

        # 7. Preparar respuesta
        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="duplicado_completo_{proyecto_id}.zip"'
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    



########################################################################################################################

@require_POST
def eliminar_categorias_masivo(request):
    try:
        ids = request.POST.getlist('ids[]')  # Obtener lista de IDs
        # Aquí implementas la lógica para eliminar múltiples categorías
        # Ejemplo:
        from .models import CategoriaNuevo
        CategoriaNuevo.objects.filter(id__in=ids).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})