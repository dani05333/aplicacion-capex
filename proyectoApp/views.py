from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.apps import apps
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# 📦 Módulos y bibliotecas
import os
import zipfile
import tempfile
import pandas as pd

# ⚙️ Modelos
from .models import (
    ProyectoNuevo, CategoriaNuevo, Adquisiciones, MaterialesOtros, EquiposConstruccion, ManoObra,
    ApuGeneral, ApuEspecifico, EspecificoCategoria, StaffEnami, DatosOtrosEP, DatosEP,
    Cantidades, ContratoSubcontrato, CotizacionMateriales, IngenieriaDetallesContraparte, GestionPermisos,
    Dueno, MB, AdministracionSupervision, PersonalIndirectoContratista, ServiciosApoyo, OtrosADM, AdministrativoFinanciero
)

# 📝 Formularios
from .forms import (
    ArchivoSubidoForm, ProyectoNuevoForm, CategoriaNuevoForm, AdquisicionesForm, MaterialesOtrosForm, 
    EquiposConstruccionForm, ManoObraForm, APUGeneralForm, APUEspecificoForm, EspecificoCategoriaForm, 
    StaffEnamiForm, DatosOtrosEPForm, DatosEPForm, CantidadesForm, ContratoSubcontratoForm, CotizacionMaterialesForm, 
    IngenieriaDetallesContraparteForm, GestionPermisosForm, DuenoForm, MBForm, AdministracionSupervisionForm, 
    PersonalIndirectoContratistaForm, ServiciosApoyoForm, OtrosADMForm, AdministrativoFinancieroForm
)

# 🔄 Funciones de Carga de Datos
from .cargar_datos import (
    cargar_proyecto_nuevo, cargar_categoria_nueva, cargar_adquisiciones, cargar_equipos_construccion, 
    cargar_mano_obra, cargar_materiales_otros, cargar_apu_especifico, cargar_apu_general, cargar_especifico_categoria, 
    cargar_staff_enami, cargar_datos_ep, cargar_datos_otros_ep, cargar_cantidades, cargar_contrato_subcontrato, 
    cargar_cotizacion_materiales, cargar_ingenieria_detalles_contraparte, cargar_gestion_permisos, cargar_dueno, 
    cargar_mb, cargar_administracion_supervision, cargar_personal_indirecto_contratista, cargar_servicios_apoyo, 
    cargar_otros_adm, cargar_administrativo_financiero
)

# 🔧 Otros Decoradores y Funciones
from rest_framework.decorators import api_view
from rest_framework.response import Response



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
            data = list(self.get_queryset().values("id", "nombre", "proyecto__nombre", "id_padre", "categoria_relacionada","nivel", "final", "total_costo"))  # ✅ Convertimos a lista de diccionarios
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
    
@csrf_exempt # Para pruebas, quitar en desarrollo
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

class ListadoAdquisiciones(ListView):
    model = Adquisiciones
    template_name = 'tabla_adquisiciones.html'
    context_object_name = 'adquisiciones'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            adquisiciones = Adquisiciones.objects.select_related('id_categoria__proyecto')
            data = []
            for a in adquisiciones:
                data.append({
                    "id": a.id,
                    "id_categoria": str(a.id_categoria) if a.id_categoria else None,
                    "proyecto": str(a.id_categoria.proyecto) if a.id_categoria and a.id_categoria.proyecto else None,
                    "tipo_origen": a.tipo_origen,
                    "tipo_categoria": a.tipo_categoria,
                    "costo_unitario": float(a.costo_unitario),
                    "crecimiento": float(a.crecimiento),
                    "flete": float(a.flete),
                    "total": float(a.total),
                    "total_con_flete": float(a.total_con_flete),
                })
            return JsonResponse(data, safe=False)
        return super().get(request, *args, **kwargs)

class ActualizarAdquisiciones(UpdateView):
    model = Adquisiciones
    form_class = AdquisicionesForm
    template_name = 'crear_adquisiciones.html'
    success_url = reverse_lazy('tabla_adquisiciones')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Adquisicion'  # Agregar título diferente para edición
        context['accion'] = 'Editar'
        return context
    
@csrf_exempt # Para pruebas, quitar en desarrollo
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
            materiales = MaterialesOtros.objects.select_related('id_categoria__proyecto')
            
            data = []
            for material in materiales:
                data.append({
                    "id": material.id,
                    "id_categoria": str(material.id_categoria),  # Para mostrar nombre
                    "proyecto": str(material.id_categoria.proyecto) if material.id_categoria and material.id_categoria.proyecto else None,
                    "costo_unidad": float(material.costo_unidad),
                    "crecimiento": float(material.crecimiento),
                    "total_usd": float(material.total_usd),
                    "fletes": float(material.fletes),
                    "total_sitio": float(material.total_sitio),
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            # Optimización: Usar select_related si hay relaciones que se deben traer en la misma consulta
            cantidades = Cantidades.objects.select_related('id_categoria')  # Si 'id_categoria' tiene una relación con otro modelo
            
            data = []
            for cantidad in cantidades:
                data.append({
                    "id": cantidad.id,
                    "id_categoria": str(cantidad.id_categoria),  # Devuelve el ID de la categoría (puedes ajustarlo a un nombre si lo deseas)
                    "proyecto": str(cantidad.id_categoria.proyecto) if cantidad.id_categoria and cantidad.id_categoria.proyecto else None,
                    "unidad_medida": cantidad.unidad_medida,
                    "cantidad": float(cantidad.cantidad),  # Asegúrate de que sea un valor numérico
                    "fc": float(cantidad.fc),  # Asegúrate de que sea un valor numérico
                    "cantidad_final": float(cantidad.cantidad_final),  # Asegúrate de que sea un valor numérico
                })
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
    
@csrf_exempt # Para pruebas, quitar en desarrollo
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
            equipos = EquiposConstruccion.objects.select_related('id_categoria__proyecto')
            data = []
            for equipo in equipos:
                data.append({
                    "id": equipo.id,
                    "id_categoria": str(equipo.id_categoria) if equipo.id_categoria else None,
                    "proyecto": str(equipo.id_categoria.proyecto) if equipo.id_categoria and equipo.id_categoria.proyecto else None,
                    "horas_maquina_unidad": float(equipo.horas_maquina_unidad),
                    "costo_maquina_hora": float(equipo.costo_maquina_hora),
                    "total_horas_maquina": float(equipo.total_horas_maquina),
                    "total_usd": float(equipo.total_usd),
                })
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

@csrf_exempt # Para pruebas, quitar en desarrollo
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
            mano_obra = ManoObra.objects.select_related('id_categoria__proyecto')

            data = []
            for mo in mano_obra:
                data.append({
                    "id": mo.id,
                    "id_categoria": str(mo.id_categoria),
                    "proyecto": str(mo.id_categoria.proyecto) if mo.id_categoria and mo.id_categoria.proyecto else None,
                    "horas_hombre_unidad": float(mo.horas_hombre_unidad),
                    "fp": float(mo.fp),
                    "rendimiento": float(mo.rendimiento),
                    "horas_hombre_final": float(mo.horas_hombre_final),
                    "cantidad_horas_hombre": float(mo.cantidad_horas_hombre),
                    "costo_hombre_hora": float(mo.costo_hombre_hora),
                    "tarifas_usd_hh_mod": float(mo.tarifas_usd_hh_mod),
                    "tarifa_usd_hh_equipos": float(mo.tarifa_usd_hh_equipos),
                    "total_hh": float(mo.total_hh),
                    "total_usd_mod": float(mo.total_usd_mod),
                    "total_usd_equipos": float(mo.total_usd_equipos),
                    "total_usd": float(mo.total_usd),
                })
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
    
@csrf_exempt # Para pruebas, quitar en desarrollo
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
            especificos = EspecificoCategoria.objects.select_related('id_categoria__proyecto')

            data = []
            for item in especificos:
                data.append({
                    "id": item.id,
                    "id_categoria": str(item.id_categoria),
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "unidad": item.unidad,
                    "cantidad": float(item.cantidad),
                    "dedicacion": float(item.dedicacion),
                    "duracion": float(item.duracion),
                    "costo": float(item.costo),
                    "total": float(item.total),
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            staff_enami_queryset = StaffEnami.objects.select_related('categoria__proyecto')  # Relacionamos la categoria y proyecto
            
            data = []
            for item in staff_enami_queryset:
                data.append({
                    "id": item.id,
                    "nombre": item.nombre,
                    "valor": float(item.valor),
                    "dotacion": float(item.dotacion),
                    "duracion": float(item.duracion),
                    "factor_utilizacion": float(item.factor_utilizacion),
                    "total_horas_hombre": float(item.total_horas_hombre),
                    "costo_total": float(item.costo_total),
                    "categoria": str(item.categoria),
                    "proyecto": str(item.categoria.proyecto) if item.categoria and item.categoria.proyecto else None,  # Incluimos el proyecto relacionado
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            proyecto_filtro = request.GET.get('proyecto', None)
            
            if proyecto_filtro:
                datos = DatosOtrosEP.objects.filter(id_categoria__proyecto__nombre=proyecto_filtro)
            else:
                datos = DatosOtrosEP.objects.all()

            data = []
            for item in datos:
                data.append({
                    "id": item.id,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "comprador": float(item.comprador) if item.comprador is not None else 0.0,
                    "dedicacion": float(item.dedicacion) if item.dedicacion is not None else 0.0,
                    "plazo": float(item.plazo) if item.plazo is not None else 0.0,
                    "sueldo_pax": float(item.sueldo_pax) if item.sueldo_pax is not None else 0.0,
                    "gestiones": float(item.gestiones) if item.gestiones is not None else 0.0,
                    "viajes": float(item.viajes) if item.viajes is not None else 0.0,
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            proyecto_filtro = request.GET.get('proyecto', None)
            
            if proyecto_filtro:
                datos = DatosEP.objects.filter(id_categoria__proyecto__nombre=proyecto_filtro)
            else:
                datos = DatosEP.objects.all()

            data = []
            for item in datos:
                data.append({
                    "id": item.id,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "hh_profesionales": float(item.hh_profesionales) if item.hh_profesionales is not None else 0.0,
                    "precio_hh": float(item.precio_hh) if item.precio_hh is not None else 0.0,
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            cotizaciones = CotizacionMateriales.objects.select_related('id_categoria__proyecto')
            data = []
            for cotizacion in cotizaciones:
                data.append({
                    "id": cotizacion.id,
                    "id_categoria": str(cotizacion.id_categoria) if cotizacion.id_categoria else None,
                    "proyecto": str(cotizacion.id_categoria.proyecto) if cotizacion.id_categoria and cotizacion.id_categoria.proyecto else None,
                    "tipo_suministro": cotizacion.tipo_suministro,
                    "tipo_moneda": cotizacion.tipo_moneda,
                    "pais_entrega": cotizacion.pais_entrega,
                    "fecha_cotizacion_referencia": cotizacion.fecha_cotizacion_referencia,
                    "cotizacion_usd": float(cotizacion.cotizacion_usd),
                    "cotizacion_clp": float(cotizacion.cotizacion_clp),
                    "factor_correccion": float(cotizacion.factor_correccion),
                    "moneda_aplicada": cotizacion.moneda_aplicada,
                    "flete_unitario": float(cotizacion.flete_unitario),
                    "origen_precio": cotizacion.origen_precio,
                    "cotizacion": cotizacion.cotizacion,
                    "moneda_origen": cotizacion.moneda_origen,
                    "tasa_cambio": float(cotizacion.tasa_cambio),
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            contratos = ContratoSubcontrato.objects.select_related('id_categoria__proyecto')
            data = []
            for contrato in contratos:
                data.append({
                    "id": contrato.id,
                    "id_categoria": str(contrato.id_categoria) if contrato.id_categoria else None,
                    "proyecto": str(contrato.id_categoria.proyecto) if contrato.id_categoria and contrato.id_categoria.proyecto else None,
                    "costo_laboral_indirecto_usd_hh": float(contrato.costo_laboral_indirecto_usd_hh),
                    "total_usd_indirectos_contratista": float(contrato.total_usd_indirectos_contratista),
                    "usd_por_unidad": float(contrato.usd_por_unidad),
                    "fc_subcontrato": float(contrato.fc_subcontrato),
                    "usd_total_subcontrato": float(contrato.usd_total_subcontrato),
                    "costo_contrato_unitario": float(contrato.costo_contrato_unitario),
                    "costo_contrato_total": float(contrato.costo_contrato_total),
                    
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            detalles = IngenieriaDetallesContraparte.objects.select_related('id_categoria__proyecto')
            data = []
            for d in detalles:
                data.append({
                    "id": d.id,
                    "id_categoria": str(d.id_categoria) if d.id_categoria else None,
                    "proyecto": str(d.id_categoria.proyecto) if d.id_categoria and d.id_categoria.proyecto else None,
                    "nombre": d.nombre,
                    "UF": float(d.UF) if d.UF is not None else 0.0,
                    "MB": float(d.MB.mb) if d.MB and d.MB.mb is not None else 0.0,
                    "total_usd": float(d.total_usd) if d.total_usd is not None else 0.0,
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            # Traemos permisos con su categoría y proyecto relacionado
            permisos = GestionPermisos.objects.select_related('id_categoria__proyecto', 'MB')
            data = []
            for permiso in permisos:
                data.append({
                    "id": permiso.id,
                    "id_categoria": str(permiso.id_categoria) if permiso.id_categoria else None,
                    "proyecto": str(permiso.id_categoria.proyecto) if permiso.id_categoria and permiso.id_categoria.proyecto else None,
                    "nombre": permiso.nombre,
                    "dedicacion": permiso.dedicacion,
                    "meses": permiso.meses,
                    "cantidad": permiso.cantidad,
                    "turno": permiso.turno,
                    "MB": float(permiso.MB.mb) if permiso.MB else 0.0,  # Accedemos al valor de MB
                    "HH": float(permiso.HH) if permiso.HH is not None else 0.0,
                    "total_clp": float(permiso.total_clp) if permiso.total_clp is not None else 0.0,  # Nuevo campo agregado
                    "total_usd": float(permiso.total_usd) if permiso.total_usd is not None else 0.0,
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            duenos = Dueno.objects.select_related('id_categoria__proyecto')
            data = []
            for d in duenos:
                data.append({
                    "id": d.id,
                    "id_categoria": str(d.id_categoria) if d.id_categoria else None,
                    "proyecto": str(d.id_categoria.proyecto) if d.id_categoria and d.id_categoria.proyecto else None,
                    "nombre": d.nombre,
                    "total_hh": float(d.total_hh),
                    "costo_hh_us": float(d.costo_hh_us),
                    "costo_total": float(d.costo_total),
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
    template_name = 'tabla_administracion_supervision.html'
    context_object_name = 'administracion_supervision'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            administracion_supervision = AdministracionSupervision.objects.select_related('id_categoria', 'mb_seleccionado')
            data = []
            for item in administracion_supervision:
                data.append({
                    "id": item.id,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "unidad": item.unidad,
                    "precio_unitario_clp": float(item.precio_unitario_clp),
                    "total_unitario": float(item.total_unitario),
                    "factor_uso": float(item.factor_uso),
                    "cantidad_u_persona": float(item.cantidad_u_persona),
                    "mb_seleccionado": float(item.mb_seleccionado.mb) if item.mb_seleccionado and item.mb_seleccionado.mb is not None else 0.0,
                    "costo_total_clp": float(item.costo_total_clp),
                    "costo_total_us": float(item.costo_total_us),
                    "costo_total_mb": float(item.costo_total_mb),
                })
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
    template_name = 'tabla_personal_indirecto_contratista.html'
    context_object_name = 'personal_indirecto_contratista'

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Filtrar por proyecto si se pasa un valor de proyecto
            proyecto_filtro = request.GET.get('proyecto', None)
            if proyecto_filtro:
                personal_indirecto_contratista = PersonalIndirectoContratista.objects.filter(proyecto__nombre=proyecto_filtro)
            else:
                personal_indirecto_contratista = PersonalIndirectoContratista.objects.all()
            
            # Obtener los datos de la consulta
            data = []
            for item in personal_indirecto_contratista:
                data.append({
                    "id": item.id,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "mb_seleccionado": float(item.mb_seleccionado.mb) if item.mb_seleccionado and item.mb_seleccionado.mb is not None else 0.0,
                    "turno": item.turno,
                    "unidad": item.unidad,
                    "hh_mes": float(item.hh_mes),
                    "plazo_mes": float(item.plazo_mes),
                    "total_hh": float(item.total_hh),
                    "precio_unitario_clp_hh": float(item.precio_unitario_clp_hh),
                    "tarifa_usd_hh": float(item.tarifa_usd_hh),
                    "costo_total_clp": float(item.costo_total_clp),
                    "costo_total_us": float(item.costo_total_us),
                    "costo_total_mb": float(item.costo_total_mb),
                })
            
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

@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            proyecto_filtro = request.GET.get('proyecto', None)
            if proyecto_filtro:
                servicios_apoyo = ServiciosApoyo.objects.filter(id_categoria__proyecto__nombre=proyecto_filtro)
            else:
                servicios_apoyo = ServiciosApoyo.objects.all()

            data = []
            for item in servicios_apoyo:
                data.append({
                    "id": item.id,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "unidad": item.unidad,
                    "cantidad": float(item.cantidad) if item.cantidad is not None else 0.0,
                    "hh_totales": float(item.hh_totales) if item.hh_totales is not None else 0.0,
                    "tarifas_clp": float(item.tarifas_clp) if item.tarifas_clp is not None else 0.0,
                    "mb": float(item.mb.mb) if item.mb and item.mb.mb is not None else 0.0,
                    "total_usd": float(item.total_usd) if item.total_usd is not None else 0.0,
                })
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
    
@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            proyecto_filtro = request.GET.get('proyecto', None)
            if proyecto_filtro:
                otros_adm = OtrosADM.objects.filter(id_categoria__proyecto__nombre=proyecto_filtro)
            else:
                otros_adm = OtrosADM.objects.all()

            data = []
            for item in otros_adm:
                data.append({
                    "id": item.id,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "HH": float(item.HH) if item.HH is not None else 0.0,
                    "MB": float(item.MB.mb) if item.MB and item.MB.mb is not None else 0.0,
                    "total_clp": float(item.total_clp) if item.total_clp is not None else 0.0,
                    "total_usd": float(item.total_usd) if item.total_usd is not None else 0.0,
                    "dedicacion": float(item.dedicacion) if item.dedicacion is not None else 0.0,
                    "meses": int(item.meses) if item.meses is not None else 0,
                    "cantidad": float(item.cantidad) if item.cantidad is not None else 0.0,
                    "turno": item.turno
                })
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
    
@csrf_exempt  # Para pruebas, quitar en desarrollo
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
            proyecto_filtro = request.GET.get('proyecto', None)

            if proyecto_filtro:
                datos = AdministrativoFinanciero.objects.filter(id_categoria__proyecto__nombre=proyecto_filtro)
            else:
                datos = AdministrativoFinanciero.objects.all()

            data = []
            for item in datos:
                data.append({
                    "id": item.id,
                    "proyecto": str(item.id_categoria.proyecto) if item.id_categoria and item.id_categoria.proyecto else None,
                    "id_categoria": str(item.id_categoria) if item.id_categoria else None,
                    "unidad": item.unidad,
                    "valor": float(item.valor) if item.valor else 0.0,
                    "meses": float(item.meses) if item.meses else 0.0,
                    "sobre_contrato_base": float(item.sobre_contrato_base) if item.sobre_contrato_base else 0.0,
                    "costo_total": float(item.costo_total) if item.costo_total else 0.0,
                })

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
    
@csrf_exempt  # Para pruebas, quitar en desarrollo
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

###############SUMA CATEGORIAS Y SUBCATEGORIAS######################################################################

def detalle_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoNuevo, id=proyecto_id)
    categorias = CategoriaNuevo.objects.filter(proyecto=proyecto, id_padre__isnull=True)  # Solo las categorías raíz

    return render(request, 'desplegable.html', {'proyecto': proyecto, 'categorias': categorias})

def obtener_subcategorias(request, categoria_id):
    """Devuelve las subcategorías de una categoría en formato JSON."""
    subcategorias = CategoriaNuevo.objects.filter(id_padre_id=categoria_id).values('id', 'nombre', 'total_costo')

    return JsonResponse(list(subcategorias), safe=False)

####ACA OBTENER SUBCATEGORIAS PARA DESPLEGABLE######################################################################

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

###################ACA RELACIONADO A SUBIR ARCHIVOS DESDE TEMPLATE##################################################
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

####################LISTAR PROYECTO PARA GRAFICO DE TORTA###########################################################

def categorias_raiz_json(request, proyecto_id):
    categorias = CategoriaNuevo.objects.filter(id_padre__isnull=True, proyecto_id=proyecto_id).values('nombre', 'total_costo')
    data = [{'name': c['nombre'], 'value': float(c['total_costo'])} for c in categorias]
    return JsonResponse(data, safe=False)

def listar_proyectos(request):
    proyectos = ProyectoNuevo.objects.values('id', 'nombre')
    return JsonResponse(list(proyectos), safe=False)

####################FUNCION PARA EXPORTAR EXCEL#####################################################################

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

####################FUNCION PARA DUPLICAR LOS PROYECTOS#############################################################

def duplicar_proyecto(request, proyecto_id):
    try:
        # 1. Configuración de modelos y campos permitidos
        MODELOS = [
            'ProyectoNuevo',
            'CategoriaNuevo'
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
    
####################FUNCION PARA ELIMINAR MASIVAMENTE LOS REGISTROS EN LA TABLA CATEGORIAS##########################

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