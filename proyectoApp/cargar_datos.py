import os
import pandas as pd
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.db import transaction
from datetime import datetime
import traceback
import numpy as np 
from .models import ProyectoNuevo, CategoriaNuevo, CostoNuevo, Adquisiciones, MaterialesOtros, EquiposConstruccion, ManoObra, ApuGeneral, ApuEspecifico, EspecificoCategoria, StaffEnami, DatosEP, DatosOtrosEP, Cantidades, ContratoSubcontrato, CotizacionMateriales, IngenieriaDetallesContraparte, GestionPermisos, Dueno, MB, AdministracionSupervision, PersonalIndirectoContratista, ServiciosApoyo, OtrosADM, AdministrativoFinanciero




def cargar_proyecto_nuevo():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'ProyectoNuevo')
    
    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                if 'nombre' not in df.columns or 'id' not in df.columns:
                    raise ValueError('El archivo debe contener las columnas "id" y "nombre".')

                for _, row in df.iterrows():
                    proyecto_id = str(row['id']).strip()
                    nombre = str(row['nombre']).strip()
                    relacionado = row.get('proyecto_relacionado', None)

                    if pd.isna(relacionado):
                        relacionado = None
                    else:
                        try:
                            relacionado = int(relacionado)
                        except (ValueError, TypeError):
                            relacionado = None

                    # Usamos update_or_create para mayor eficiencia
                    proyecto, created = ProyectoNuevo.objects.update_or_create(
                        id=proyecto_id,
                        defaults={
                            'nombre': nombre,
                            'proyecto_relacionado': relacionado,
                            # No establecemos costo_total aquí, se calculará después
                        }
                    )

                    # Si el Excel trae costo_total, lo usamos (opcional)
                    if 'costo_total' in row and not pd.isna(row['costo_total']):
                        proyecto.costo_total = Decimal(str(row['costo_total']))
                        proyecto.save(skip_cost_recalculation=True)
                    elif created:
                        # Solo calcular si es nuevo proyecto
                        proyecto.calcular_costo_total(save=True)

                print(f'Archivo {archivo} cargado exitosamente.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {str(e)}')


                
def cargar_categoria_nueva():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'CategoriaNuevo')

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                # Leer el Excel especificando el tipo de dato para id_padre como string
                df = pd.read_excel(ruta_archivo, dtype={'id': str, 'id_padre': str, 'categoria_relacionada': str})

                # Verificar columnas requeridas
                columnas_requeridas = {'id', 'nombre', 'proyecto', 'id_padre', 'categoria_relacionada', 'final', 'nivel'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f"El archivo debe contener las columnas {columnas_requeridas}.")

                # Ordenar por nivel para asegurar carga de padres antes que hijos
                df = df.sort_values(by=['nivel'])

                # Diccionario para almacenar las categorías creadas
                categorias_creadas = {}
                proyectos_cache = {}

                for _, row in df.iterrows():
                    try:
                        # Cache de proyectos para mejor performance
                        proyecto_id = str(row['proyecto'])  # Asegurar que es string
                        if proyecto_id not in proyectos_cache:
                            proyectos_cache[proyecto_id] = ProyectoNuevo.objects.get(id=proyecto_id)
                        proyecto = proyectos_cache[proyecto_id]

                        # Manejo robusto de id_padre
                        id_padre = None
                        if pd.notna(row['id_padre']):
                            id_padre = str(row['id_padre']).strip()  # Convertir a string y limpiar espacios
                            
                            # Si el ID es un número decimal (ej: "4000.0"), lo convertimos a entero primero
                            if '.' in id_padre and id_padre.split('.')[1] == '0':
                                id_padre = id_padre.split('.')[0]
                            
                            if id_padre in categorias_creadas:
                                id_padre = categorias_creadas[id_padre]
                            else:
                                try:
                                    id_padre = CategoriaNuevo.objects.get(id=id_padre)
                                except CategoriaNuevo.DoesNotExist:
                                    print(f"Advertencia: La categoría padre con ID {id_padre} no existe aún.")
                                    id_padre = None

                        # Convertir 'final' a booleano
                        es_final = bool(row['final']) if pd.notna(row['final']) else False

                        # Manejo de categoria_relacionada
                        categoria_relacionada = str(row['categoria_relacionada']).strip() if pd.notna(row['categoria_relacionada']) else None
                        if categoria_relacionada and '.' in categoria_relacionada and categoria_relacionada.split('.')[1] == '0':
                            categoria_relacionada = categoria_relacionada.split('.')[0]

                        # Crear o actualizar la categoría
                        categoria_id = str(row['id']).strip()
                        if '.' in categoria_id and categoria_id.split('.')[1] == '0':
                            categoria_id = categoria_id.split('.')[0]

                        categoria, created = CategoriaNuevo.objects.update_or_create(
                            id=categoria_id,
                            defaults={
                                'nombre': row['nombre'],
                                'proyecto': proyecto,
                                'id_padre': id_padre,
                                'categoria_relacionada': categoria_relacionada,
                                'final': es_final,
                                'nivel': int(row['nivel']) if pd.notna(row['nivel']) else 1
                            }
                        )

                        # Guardar en el diccionario de categorías creadas
                        categorias_creadas[categoria_id] = categoria

                    except ProyectoNuevo.DoesNotExist:
                        print(f"Error: El proyecto con ID {row['proyecto']} no existe.")
                    except Exception as e:
                        print(f"Error al procesar categoría {row.get('id')}: {str(e)}")
                        continue

                print(f"Archivo {archivo} cargado exitosamente. Categorías procesadas: {len(categorias_creadas)}")

            except Exception as e:
                print(f"Error al procesar el archivo {archivo}: {e}")



def cargar_costo_nuevo():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'CostoNuevo')
    
    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                # Validar que las columnas esperadas existen
                if not all(col in df.columns for col in ['categoria']):
                    raise ValueError('El archivo debe contener la columna "categoria".')

                # Empezamos una transacción para asegurar la atomicidad de la operación
                with transaction.atomic():
                    for _, row in df.iterrows():
                        try:
                            categoria = CategoriaNuevo.objects.get(id=row['categoria'])

                            # Verificar si el CostoNuevo ya existe para esta categoría
                            if not CostoNuevo.objects.filter(categoria=categoria).exists():
                                # Crear el objeto CostoNuevo
                                costo_nuevo = CostoNuevo(categoria=categoria)
                                costo_nuevo.save()  # Guarda el objeto, lo que activará el cálculo de 'monto'

                        except CategoriaNuevo.DoesNotExist:
                            print(f'Error: La categoría con ID {row["categoria"]} no existe.')

                print(f'Archivo {archivo} cargado exitosamente.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {e}')





def cargar_adquisiciones():
    # Directorio donde se encuentran los archivos Excel
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'Adquisiciones')

    # Recorrer todos los archivos en el directorio
    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                # Leer el archivo Excel
                df = pd.read_excel(ruta_archivo)

                # Validar que las columnas requeridas existen
                columnas_requeridas = ['id_categoria', 'tipo_origen', 'tipo_categoria', 'costo_unitario', 'crecimiento']
                if not all(col in df.columns for col in columnas_requeridas):
                    raise ValueError(f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')

                # Recorrer cada fila del DataFrame
                for _, row in df.iterrows():
                    try:
                        # Obtener la categoría asociada
                        id_categoria = row['id_categoria']
                        categoria = CategoriaNuevo.objects.get(id=id_categoria)

                        # Obtener cantidad relacionada
                        cantidad = Cantidades.objects.filter(id_categoria=categoria).first()
                        cantidad_final = Decimal(cantidad.cantidad_final) if cantidad else Decimal('0.00')

                        # Obtener flete_unitario desde CotizacionMateriales
                        cotizacion = CotizacionMateriales.objects.filter(id_categoria=categoria).first()
                        flete_unitario = Decimal(cotizacion.flete_unitario) if cotizacion else Decimal('0.00')

                        # Convertir valores a Decimal
                        costo_unitario = Decimal(str(row['costo_unitario']))
                        crecimiento = Decimal(str(row['crecimiento']))

                        # Validar valores negativos
                        if crecimiento < 0:
                            raise ValueError(f'El valor de crecimiento no puede ser negativo en la fila {row}')

                        # Calcular total con crecimiento
                        if crecimiento > 0:
                            total = cantidad_final * costo_unitario * (1 + crecimiento / 100)
                        else:
                            total = cantidad_final * costo_unitario

                        # Calcular flete como porcentaje del total
                        flete = total * (flete_unitario / 100)

                        # Calcular total con flete
                        total_con_flete = total + flete

                        # Crear o actualizar la adquisición
                        Adquisiciones.objects.get_or_create(
                            id_categoria=categoria,
                            tipo_origen=row['tipo_origen'],
                            tipo_categoria=row['tipo_categoria'],
                            defaults={
                                'costo_unitario': costo_unitario,
                                'total': total,
                                'crecimiento': crecimiento,
                                'flete': flete,  # Calculado, no ingresado desde Excel
                                'total_con_flete': total_con_flete  # Calculado
                            }
                        )

                    except CategoriaNuevo.DoesNotExist:
                        print(f'Error: La categoría con ID {id_categoria} no existe.')
                    except ValueError as e:
                        print(f'Error en la fila {row}: {e}')
                    except Exception as e:
                        print(f'Error al procesar la fila {row}: {e}')

                print(f'Archivo {archivo} cargado exitosamente.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {e}')


def cargar_cantidades():
    # Directorio donde se encuentran los archivos Excel
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'Cantidades')

    # Recorrer todos los archivos en el directorio
    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                # Leer el archivo Excel
                df = pd.read_excel(ruta_archivo)

                # Verificar columnas requeridas
                columnas_requeridas = {'id_categoria', 'unidad_medida', 'cantidad', 'fc'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f"El archivo debe contener las columnas {columnas_requeridas}.")

                # Recorrer cada fila del DataFrame
                for _, row in df.iterrows():
                    try:
                        # Obtener la categoría asociada
                        id_categoria = row['id_categoria']
                        categoria = CategoriaNuevo.objects.get(id=id_categoria)

                        # Calcular cantidad_final
                        cantidad = Decimal(str(row['cantidad']))  # Convertir a Decimal
                        fc = Decimal(str(row['fc']))  # Convertir a Decimal
                        cantidad_final = cantidad + (cantidad * (fc / Decimal('100')))

                        # Crear o actualizar la cantidad
                        Cantidades.objects.get_or_create(
                            id_categoria=categoria,
                            defaults={
                                'unidad_medida': row['unidad_medida'],
                                'cantidad': cantidad,
                                'fc': fc,
                                'cantidad_final': cantidad_final
                            }
                        )

                    except CategoriaNuevo.DoesNotExist:
                        print(f"Error: La categoría con ID {id_categoria} no existe.")
                    except Exception as e:
                        print(f"Error al procesar la fila {row}: {e}")

                print(f"Archivo {archivo} cargado exitosamente.")

            except Exception as e:
                print(f"Error al procesar el archivo {archivo}: {e}")



def cargar_materiales_otros():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'MaterialesOtros')

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo, dtype={'id_categoria': str})  # Forzar a string

                # Validar que las columnas requeridas existen en el archivo (sin flete_unitario)
                columnas_requeridas = ['id_categoria', 'costo_unidad', 'crecimiento']
                if not all(col in df.columns for col in columnas_requeridas):
                    raise ValueError(f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')

                for _, row in df.iterrows():
                    try:
                        id_categoria = row['id_categoria']  # Asegurar que sea entero
                        categoria = CategoriaNuevo.objects.get(id=id_categoria)

                        # Obtener cantidad_final de Cantidades
                        cantidad = Cantidades.objects.filter(id_categoria=categoria).first()
                        cantidad_final = cantidad.cantidad_final if cantidad else Decimal('0')

                        # Convertir valores a Decimal y manejar valores nulos
                        costo_unidad = Decimal(str(row['costo_unidad']).replace(',', '.'))
                        crecimiento = Decimal(str(row['crecimiento']).replace(',', '.')) if row['crecimiento'] else Decimal('0')

                        # Obtener flete_unitario desde CotizacionMateriales
                        cotizacion = CotizacionMateriales.objects.filter(id_categoria=categoria).first()
                        flete_unitario = cotizacion.flete_unitario if cotizacion else Decimal('0')

                        # Calcular total_usd con crecimiento
                        if crecimiento > 0:
                            total_usd = cantidad_final * costo_unidad * (1 + crecimiento / 100)
                        else:
                            total_usd = cantidad_final * costo_unidad

                        # Calcular fletes y total_sitio
                        fletes = total_usd * (flete_unitario / 100)
                        total_sitio = total_usd + fletes

                        # Crear o actualizar MaterialesOtros
                        material, created = MaterialesOtros.objects.get_or_create(
                            id_categoria=categoria,
                            defaults={
                                'costo_unidad': costo_unidad,
                                'crecimiento': crecimiento,
                                'total_usd': total_usd,
                                'fletes': fletes,
                                'total_sitio': total_sitio
                            }
                        )

                    except CategoriaNuevo.DoesNotExist:
                        print(f'Error: La categoría con ID {id_categoria} no existe.')

                print(f'Archivo {archivo} cargado exitosamente.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {e}')



def cargar_equipos_construccion():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'EquiposConstruccion')

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo, dtype={'id_categoria': str})  # Forzar a string

                # Validar que las columnas esperadas existen
                columnas_requeridas = ['id_categoria', 'horas_maquina_unidad', 'costo_maquina_hora']
                if not all(col in df.columns for col in columnas_requeridas):
                    raise ValueError(f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')

                for _, row in df.iterrows():
                    try:
                        # Convertir id_categoria a int para evitar el float
                        id_categoria = row['id_categoria']

                        # Obtener la categoría
                        categoria = CategoriaNuevo.objects.get(id=id_categoria)

                        # Obtener cantidad_final de la tabla Cantidades
                        cantidad = Cantidades.objects.filter(id_categoria=categoria).first()
                        cantidad_final = cantidad.cantidad_final if cantidad else Decimal(0)

                        # Convertir valores numéricos a Decimal
                        horas_maquina_unidad = Decimal(str(row['horas_maquina_unidad']))
                        costo_maquina_hora = Decimal(str(row['costo_maquina_hora']))

                        # ✅ Aplicar la lógica corregida para `total_usd`
                        if categoria.final:
                            total_usd = costo_maquina_hora * cantidad_final * horas_maquina_unidad  # 3 columnas si final=True
                        else:
                            total_usd = costo_maquina_hora * cantidad_final  # 2 columnas si final=False

                        # Crear o actualizar el objeto en la base de datos
                        equipo, created = EquiposConstruccion.objects.get_or_create(
                            id_categoria=categoria,
                            defaults={
                                'horas_maquina_unidad': horas_maquina_unidad,
                                'costo_maquina_hora': costo_maquina_hora,
                                'total_horas_maquina': horas_maquina_unidad * cantidad_final,
                                'total_usd': total_usd
                            }
                        )

                        

                    except CategoriaNuevo.DoesNotExist:
                        print(f'Error: La categoría con ID {id_categoria} no existe.')

                print(f'Archivo {archivo} cargado exitosamente.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {e}')

                




def cargar_mano_obra():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'ManoObra')
    
    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo, dtype={'id_categoria': str})  # Forzar a string
                
                columnas_requeridas = ['id_categoria', 'horas_hombre_unidad', 'fp', 'costo_hombre_hora', 'rendimiento', 'tarifas_usd_hh_mod','tarifa_usd_hh_equipos']
                if not all(col in df.columns for col in columnas_requeridas):
                    raise ValueError(f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')

                for _, row in df.iterrows():
                    try:
                        id_categoria = row['id_categoria']
                        categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        horas_hombre_unidad = Decimal(str(row['horas_hombre_unidad']))
                        fp = Decimal(str(row['fp']))
                        costo_hombre_hora = Decimal(str(row['costo_hombre_hora']))
                        rendimiento = Decimal(str(row['rendimiento']))
                        tarifas_usd_hh_mod = Decimal(str(row['tarifas_usd_hh_mod']))
                        tarifa_usd_hh_equipos = Decimal(str(row['tarifa_usd_hh_equipos']))

                        cantidad = Cantidades.objects.filter(id_categoria=categoria).first()
                        cantidad_final = cantidad.cantidad_final if cantidad else Decimal(0)

                        horas_hombre_final = horas_hombre_unidad * fp
                        total_hh = cantidad_final * rendimiento * fp
                        cantidad_horas_hombre = horas_hombre_final * cantidad_final
                        total_usd_mod = total_hh * tarifas_usd_hh_mod
                        total_usd_equipos = total_hh * tarifa_usd_hh_equipos

                        if total_usd_mod == 0 and total_usd_equipos == 0:
                            total_usd = cantidad_final * horas_hombre_final * costo_hombre_hora
                        else:
                            total_usd = total_usd_equipos + total_usd_mod

                        ManoObra.objects.get_or_create(
                            id_categoria=categoria,
                            defaults={
                                'horas_hombre_unidad': horas_hombre_unidad,
                                'fp': fp,
                                'costo_hombre_hora': costo_hombre_hora,
                                'rendimiento': rendimiento,
                                'tarifas_usd_hh_mod': tarifas_usd_hh_mod,
                                'tarifa_usd_hh_equipos': tarifa_usd_hh_equipos,
                                'horas_hombre_final': horas_hombre_final,
                                'total_hh': total_hh,
                                'cantidad_horas_hombre': cantidad_horas_hombre,
                                'total_usd_mod': total_usd_mod,
                                'total_usd_equipos': total_usd_equipos,
                                'total_usd': total_usd
                            }
                        )

                        

                    except CategoriaNuevo.DoesNotExist:
                        print(f'Error: La categoría con ID {id_categoria} no existe.')

                print(f'Archivo {archivo} cargado exitosamente.')
            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {e}')




                

def cargar_apu_general():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'ApuGeneral')

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)
                if 'nombre' not in df.columns:
                    raise ValueError('El archivo debe contener la columna "nombre"')
                
                for _, row in df.iterrows():
                    ApuGeneral.objects.get_or_create(nombre=row['nombre'])

                print(f'Archivo {archivo} cargado exitosamente.')
            except Exception as e:
                print(f'Error al procesar el archivo {archivo}: {e}')

def cargar_apu_especifico():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'ApuEspecifico')

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)
                columnas_requeridas = ['id_apu_general', 'id_mano_obra', 'nombre', 'unidad_medida', 'cantidad', 'precio_unitario','id_categoria']
                if not all(col in df.columns for col in columnas_requeridas):
                    raise ValueError(f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')

                for _, row in df.iterrows():
                    try:
                        apu_general = ApuGeneral.objects.get(id=int(row['id_apu_general']))
                        mano_obra = ManoObra.objects.get(id=int(row['id_mano_obra']))
                        categoria = CategoriaNuevo.objects.get(id=int(row['id_categoria']))

                        # 🔹 Buscar si ya existe el registro
                        apu_especifico, creado = ApuEspecifico.objects.get_or_create(
                            id_apu_general=apu_general,
                            id_mano_obra=mano_obra,
                            id_categoria=categoria,
                            nombre=row['nombre'],  # Clave única junto con las otras FK
                            defaults={
                                "unidad_medida": row['unidad_medida'],
                                "cantidad": Decimal(str(row['cantidad'])),
                                "precio_unitario": Decimal(str(row['precio_unitario']))
                            }
                        )

                        if apu_general.id == 1:
                            mano_obra.actualizar_costo_hombre_hora()
                    except (ApuGeneral.DoesNotExist, ManoObra.DoesNotExist):
                        print(f' Error: ApuGeneral o ManoObra no encontrado para ID en fila {row}')

                print(f' Archivo {archivo} procesado correctamente.')
            except Exception as e:
                print(f' Error al procesar el archivo {archivo}: {e}')



def cargar_especifico_categoria():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'EspecificoCategoria')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                # Verificar si el archivo tiene las columnas necesarias
                columnas_requeridas = {'id_categoria', 'unidad', 'cantidad', 'dedicacion', 'duracion', 'costo'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo {archivo} debe contener las columnas {columnas_requeridas}')

                for _, row in df.iterrows():
                    try:
                        id_categoria = CategoriaNuevo.objects.get(id=row['id_categoria'])
                    except CategoriaNuevo.DoesNotExist:
                        print(f'Categoría con id {row["id_categoria"]} no encontrada. Saltando fila...')
                        continue

                    # Convertir valores a Decimal para evitar errores
                    cantidad = Decimal(str(row['cantidad'])) if pd.notna(row['cantidad']) else Decimal('0')
                    dedicacion = Decimal(str(row['dedicacion'])) if pd.notna(row['dedicacion']) else Decimal('0')
                    duracion = Decimal(str(row['duracion'])) if pd.notna(row['duracion']) else Decimal('0')
                    costo = Decimal(str(row['costo'])) if pd.notna(row['costo']) else Decimal('0')

                    # Calcular el total
                    total = cantidad * duracion * (dedicacion / Decimal('100')) * costo

                    # Guardar en la base de datos
                    EspecificoCategoria.objects.get_or_create(
                        id_categoria=id_categoria,
                        unidad=row['unidad'],
                        cantidad=cantidad,
                        dedicacion=dedicacion,
                        duracion=duracion,
                        costo=costo,
                        defaults={'total': total}
                    )

                print(f'Archivo {archivo} cargado exitosamente en EspecificoCategoria.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo} para EspecificoCategoria: {e}')


def cargar_staff_enami():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'StaffEnami')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                # Verificar que el archivo tenga las columnas necesarias
                columnas_requeridas = {'categoria', 'nombre', 'valor', 'dotacion', 'duracion', 'factor_utilizacion'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo {archivo} debe contener las columnas {columnas_requeridas}')

                for _, row in df.iterrows():
                    try:
                        categoria = CategoriaNuevo.objects.get(id=row['categoria'])
                    except CategoriaNuevo.DoesNotExist:
                        print(f'Categoría con id {row["categoria"]} no encontrada. Saltando fila...')
                        continue

                    # Normalizar valores antes de comparar
                    nombre = row['nombre'].strip().lower()
                    valor = Decimal(row['valor']).quantize(Decimal('0.00'))
                    factor_utilizacion = Decimal(row['factor_utilizacion']).quantize(Decimal('0.00'))
                    dotacion = int(row['dotacion'])
                    duracion = int(row['duracion'])

                    # Buscar si el registro ya existe con los mismos valores
                    staff_existente = StaffEnami.objects.filter(
                        nombre=nombre,
                        categoria=categoria
                    ).first()

                    if staff_existente:
                        # Solo actualizar si hay cambios en los valores
                        if (
                            staff_existente.valor != valor or
                            staff_existente.dotacion != dotacion or
                            staff_existente.duracion != duracion or
                            staff_existente.factor_utilizacion != factor_utilizacion
                        ):
                            staff_existente.valor = valor
                            staff_existente.dotacion = dotacion
                            staff_existente.duracion = duracion
                            staff_existente.factor_utilizacion = factor_utilizacion
                            staff_existente.save()
                    else:
                        # Crear nuevo registro si no existe
                        StaffEnami.objects.create(
                            nombre=nombre,
                            categoria=categoria,
                            valor=valor,
                            dotacion=dotacion,
                            duracion=duracion,
                            factor_utilizacion=factor_utilizacion,
                        )

                print(f'Archivo {archivo} cargado exitosamente en StaffEnami.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo} para StaffEnami: {e}')




def cargar_datos_ep():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'DatosEP')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                # Verificar que el archivo tenga las columnas necesarias
                columnas_requeridas = {'id', 'hh_profesionales', 'precio_hh', 'id_categoria'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo {archivo} debe contener las columnas {columnas_requeridas}')

                for _, row in df.iterrows():
                    try:
                        categoria = CategoriaNuevo.objects.get(id=row['id_categoria'])
                    except CategoriaNuevo.DoesNotExist:
                        print(f'Categoría con id {row["id_categoria"]} no encontrada. Saltando fila...')
                        continue

                    # Convertir a string y luego a Decimal para evitar errores
                    hh_profesionales = Decimal(str(row['hh_profesionales']))
                    precio_hh = Decimal(str(row['precio_hh']))

                    # Crear o actualizar el objeto DatosEP
                    datos_ep, created = DatosEP.objects.get_or_create(
                        id=row['id'],  # ID personalizado
                        id_categoria=categoria,
                        defaults={
                            'hh_profesionales': hh_profesionales,
                            'precio_hh': precio_hh,
                        }
                    )

                print(f'Archivo {archivo} cargado exitosamente en DatosEP.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo} para DatosEP: {e}')




def cargar_datos_otros_ep():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'DatosOtrosEP')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                # Verificar columnas necesarias
                columnas_requeridas = {'comprador', 'dedicacion', 'plazo', 'sueldo_pax', 'viajes', 'id_categoria'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo {archivo} debe contener las columnas {columnas_requeridas}')

                for _, row in df.iterrows():
                    try:
                        categoria = CategoriaNuevo.objects.get(id=row['id_categoria'])
                    except CategoriaNuevo.DoesNotExist:
                        print(f'Categoría con id {row["id_categoria"]} no encontrada. Saltando fila...')
                        continue

                    # Convertir valores
                    comprador = int(row['comprador'])
                    dedicacion = Decimal(str(row['dedicacion']))
                    plazo = Decimal(str(row['plazo']))
                    sueldo_pax = Decimal(str(row['sueldo_pax']))
                    viajes = Decimal(str(row['viajes']))

                    # Verificar si el registro ya existe antes de insertarlo
                    if not DatosOtrosEP.objects.filter(
                        id_categoria=categoria,
                        comprador=comprador,
                        dedicacion=dedicacion,
                        plazo=plazo,
                        sueldo_pax=sueldo_pax,
                        viajes=viajes
                    ).exists():
                        DatosOtrosEP.objects.create(
                            id_categoria=categoria,
                            comprador=comprador,
                            dedicacion=dedicacion,
                            plazo=plazo,
                            sueldo_pax=sueldo_pax,
                            viajes=viajes
                        )

                print(f'Archivo {archivo} cargado exitosamente en DatosOtrosEP.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo} para DatosOtrosEP: {e}')


def cargar_contrato_subcontrato():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'ContratoSubcontrato')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo forzando id_categoria como string
                df = pd.read_excel(ruta_archivo, dtype={'id_categoria': str})
                
                # Validar columnas requeridas
                columnas_requeridas = {'id_categoria', 'costo_laboral_indirecto_usd_hh', 'fc_subcontrato'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: eliminar espacios y convertir a string
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                
                # Obtener lista de categorías ya existentes en la base de datos
                categorias_existentes = set(ContratoSubcontrato.objects.values_list('id_categoria__id', flat=True))
                
                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    
                    # Verificar si la categoría ya existe
                    if id_categoria in categorias_existentes:
                        omitidos += 1
                        continue
                        
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            omitidos += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            omitidos += 1
                            continue

                        # Función para convertir valores a Decimal de forma segura
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores principales
                        costo_laboral = to_decimal(row['costo_laboral_indirecto_usd_hh'])
                        fc_subcontrato = to_decimal(row['fc_subcontrato'])

                        # Obtener datos relacionados
                        cantidad = Cantidades.objects.filter(id_categoria=categoria).first()
                        mano_obra = ManoObra.objects.filter(id_categoria=categoria).first()
                        materiales_otros = MaterialesOtros.objects.filter(id_categoria=categoria).first()
                        cotizacion = CotizacionMateriales.objects.filter(id_categoria=categoria).first()

                        # Calcular campos derivados
                        total_hh = mano_obra.total_hh if mano_obra else Decimal('0')
                        total_usd_indirectos_contratista = total_hh + costo_laboral

                        moneda_aplicada = cotizacion.moneda_aplicada if cotizacion else Decimal('0')
                        usd_por_unidad = moneda_aplicada * (1 + fc_subcontrato / 100)

                        cantidad_final = cantidad.cantidad_final if cantidad else Decimal('0')
                        usd_total_subcontrato = cantidad_final * usd_por_unidad

                        total_sitio = materiales_otros.total_sitio if materiales_otros else Decimal('0')
                        total_usd_mano_obra = mano_obra.total_usd if mano_obra else Decimal('0')
                        
                        costo_contrato_total = usd_total_subcontrato + total_usd_indirectos_contratista + total_sitio + total_usd_mano_obra
                        
                        costo_contrato_unitario = (
                            costo_contrato_total / cantidad_final 
                            if cantidad_final > 0 
                            else Decimal('0')
                        )

                        # Crear nuevo registro
                        print(f"Creando nuevo contrato para categoría {id_categoria}")
                        ContratoSubcontrato.objects.create(
                            id_categoria=categoria,
                            costo_laboral_indirecto_usd_hh=costo_laboral,
                            fc_subcontrato=fc_subcontrato,
                            total_usd_indirectos_contratista=total_usd_indirectos_contratista,
                            usd_por_unidad=usd_por_unidad,
                            usd_total_subcontrato=usd_total_subcontrato,
                            costo_contrato_total=costo_contrato_total,
                            costo_contrato_unitario=costo_contrato_unitario
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        omitidos += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')


def cargar_cotizacion_materiales():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'CotizacionMateriales')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo forzando id_categoria como string
                df = pd.read_excel(ruta_archivo, dtype={'id_categoria': str})
                
                # Validar columnas requeridas
                columnas_requeridas = {
                    'id_categoria', 'tipo_suministro', 'tipo_moneda', 'pais_entrega', 
                    'fecha_cotizacion_referencia', 'cotizacion_usd', 'cotizacion_clp', 
                    'factor_correccion', 'moneda_aplicada', 'origen_precio', 'cotizacion', 
                    'moneda_origen', 'tasa_cambio', 'flete_unitario'
                }
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: eliminar espacios y convertir a string
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                
                # Obtener lista de categorías ya existentes en la base de datos
                categorias_existentes = set(CotizacionMateriales.objects.values_list('id_categoria__id', flat=True))
                
                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0

                # Convertir la columna de fecha asegurando que sea válida
                df['fecha_cotizacion_referencia'] = pd.to_datetime(
                    df['fecha_cotizacion_referencia'], 
                    format='%d-%m-%Y', 
                    errors='coerce'
                )

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    
                    # Verificar si la categoría ya existe
                    if id_categoria in categorias_existentes:
                        omitidos += 1
                        continue
                        
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            omitidos += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            omitidos += 1
                            continue

                        # Función para convertir valores a Decimal de forma segura
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        cotizacion_usd = to_decimal(row['cotizacion_usd'])
                        cotizacion_clp = to_decimal(row['cotizacion_clp'])
                        factor_correccion = to_decimal(row['factor_correccion'])
                        tasa_cambio = to_decimal(row['tasa_cambio'])
                        flete_unitario = to_decimal(row['flete_unitario'])
                        
                        # Manejar campo de texto
                        cotizacion = str(row['cotizacion']) if pd.notna(row['cotizacion']) else ''

                        # Validar la fecha
                        fecha_cotizacion = row['fecha_cotizacion_referencia']
                        if pd.isna(fecha_cotizacion):
                            print(f'Fila {index+2}: Fecha inválida. Asignando fecha actual.')
                            fecha_cotizacion = datetime.today()
                        else:
                            fecha_cotizacion = fecha_cotizacion.to_pydatetime()

                        # Crear nuevo registro
                        print(f"Creando nueva cotización para categoría {id_categoria}")
                        CotizacionMateriales.objects.create(
                            id_categoria=categoria,
                            tipo_suministro=row['tipo_suministro'],
                            tipo_moneda=row['tipo_moneda'],
                            pais_entrega=row['pais_entrega'],
                            fecha_cotizacion_referencia=fecha_cotizacion,
                            cotizacion_usd=cotizacion_usd,
                            cotizacion_clp=cotizacion_clp,
                            factor_correccion=factor_correccion,
                            moneda_aplicada=row['moneda_aplicada'],
                            origen_precio=row['origen_precio'],
                            cotizacion=cotizacion,
                            moneda_origen=row['moneda_origen'],
                            tasa_cambio=tasa_cambio,
                            flete_unitario=flete_unitario
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        omitidos += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')


def cargar_ingenieria_detalles_contraparte():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'IngenieriaDetallesContraparte')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo forzando id_categoria como string
                df = pd.read_excel(ruta_archivo, dtype={'id_categoria': str, 'MB': str})
                
                # Validar columnas requeridas
                columnas_requeridas = {'id_categoria', 'nombre', 'UF', 'MB'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de strings
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['nombre'] = df['nombre'].astype(str).str.strip()
                df['MB'] = df['MB'].astype(str).str.strip()
                
                # Obtener lista de combinaciones únicas (id_categoria, nombre) ya existentes
                existentes = set(IngenieriaDetallesContraparte.objects.values_list(
                    'id_categoria__id', 'nombre'
                ))
                
                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    nombre = row['nombre']
                    
                    # Verificar si el registro ya existe (combinación id_categoria + nombre)
                    if (id_categoria, nombre) in existentes:
                        omitidos += 1
                        continue
                        
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            omitidos += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            omitidos += 1
                            continue

                        # Función para convertir valores a Decimal de forma segura
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores
                        UF = to_decimal(row['UF'])
                        
                        # Validar nombre
                        nombre = nombre if nombre else 'Sin Nombre'

                        # Manejar campo MB
                        mb_obj = None
                        mb_id = row['MB']
                        if mb_id and mb_id != 'nan' and mb_id != 'None':
                            try:
                                mb_obj = MB.objects.get(id=int(float(mb_id)))  # Conversión segura a int
                            except (MB.DoesNotExist, ValueError):
                                print(f"Fila {index+2}: MB con ID '{mb_id}' no encontrado - usando None")
                                mb_obj = None

                        # Crear nuevo registro
                        print(f"Creando nuevo detalle para categoría {id_categoria} - {nombre}")
                        IngenieriaDetallesContraparte.objects.create(
                            id_categoria=categoria,
                            nombre=nombre,
                            UF=UF,
                            MB=mb_obj
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        omitidos += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')




def cargar_gestion_permisos():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'GestionPermisos')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo forzando tipos de datos adecuados
                df = pd.read_excel(ruta_archivo, dtype={
                    'id_categoria': str,
                    'MB': str,
                    'nombre': str,
                    'turno': str
                })
                
                # Validar columnas requeridas
                columnas_requeridas = {'id_categoria', 'nombre', 'dedicacion', 'meses', 'cantidad', 'turno', 'MB'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de strings
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['nombre'] = df['nombre'].astype(str).str.strip()
                df['turno'] = df['turno'].astype(str).str.strip()
                df['MB'] = df['MB'].astype(str).str.strip()
                
                # Obtener lista de registros existentes (id_categoria + nombre como clave única)
                existentes = set(GestionPermisos.objects.values_list(
                    'id_categoria__id', 'nombre'
                ))
                
                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    nombre = row['nombre']
                    
                    # Verificar si el registro ya existe
                    if (id_categoria, nombre) in existentes:
                        omitidos += 1
                        continue
                        
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            omitidos += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            omitidos += 1
                            continue

                        # Función para convertir valores numéricos de forma segura
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        dedicacion = to_decimal(row['dedicacion'])
                        
                        # Convertir valores enteros
                        try:
                            meses = int(row['meses']) if pd.notna(row['meses']) else 0
                            cantidad = int(row['cantidad']) if pd.notna(row['cantidad']) else 0
                        except ValueError:
                            print(f"Fila {index+2}: Valor inválido para meses/cantidad - usando 0 por defecto")
                            meses = cantidad = 0

                        # Validar campo turno
                        turno = row['turno'] if row['turno'] and str(row['turno']).strip() != 'nan' else 'No especificado'

                        # Manejar campo MB
                        mb_obj = None
                        mb_id = row['MB']
                        if mb_id and mb_id != 'nan' and mb_id != 'None':
                            try:
                                mb_obj = MB.objects.get(id=int(float(mb_id)))  # Conversión segura a int
                            except (MB.DoesNotExist, ValueError):
                                print(f"Fila {index+2}: MB con ID '{mb_id}' no encontrado - usando None")
                                mb_obj = None

                        # Calcular HH y total_usd
                        HH = (dedicacion / 100) * meses * cantidad * 180
                        total_usd = HH * mb_obj.mb if mb_obj else Decimal('0')

                        # Crear nuevo registro
                        print(f"Creando nuevo permiso para categoría {id_categoria} - {nombre}")
                        GestionPermisos.objects.create(
                            id_categoria=categoria,
                            nombre=nombre,
                            dedicacion=dedicacion,
                            meses=meses,
                            cantidad=cantidad,
                            turno=turno,
                            MB=mb_obj,
                            HH=HH,
                            total_usd=total_usd
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        omitidos += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')



def cargar_dueno():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'Dueno')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo forzando tipos de datos adecuados
                df = pd.read_excel(ruta_archivo, dtype={
                    'id_categoria': str,
                    'nombre': str,
                    'total_hh': str,
                    'costo_hh_us': str
                })

                # Validar columnas requeridas
                columnas_requeridas = {'id_categoria', 'nombre', 'total_hh', 'costo_hh_us'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de strings
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['nombre'] = df['nombre'].astype(str).str.strip()

                # Obtener lista de registros existentes (id_categoria + nombre como clave única)
                existentes = set(Dueno.objects.values_list(
                    'id_categoria__id', 'nombre'
                ))

                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    nombre = row['nombre']

                    # Verificar si el registro ya existe
                    if (id_categoria, nombre) in existentes:
                        omitidos += 1
                        continue

                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            omitidos += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            omitidos += 1
                            continue

                        # Función para convertir valores numéricos de forma segura
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        total_hh = to_decimal(row['total_hh'])
                        costo_hh_us = to_decimal(row['costo_hh_us'])
                        costo_total = total_hh * costo_hh_us

                        # Crear nuevo registro
                        print(f"Creando nuevo dueño para categoría {id_categoria} - {nombre}")
                        Dueno.objects.create(
                            id_categoria=categoria,
                            nombre=nombre,
                            total_hh=total_hh,
                            costo_hh_us=costo_hh_us,
                            costo_total=costo_total
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        omitidos += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')


def cargar_mb():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'MB')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo forzando tipos de datos adecuados
                df = pd.read_excel(ruta_archivo, dtype={'id': str, 'mb': str, 'fc': str, 'anio': str})

                # Validar columnas requeridas
                columnas_requeridas = {'id', 'mb', 'fc', 'anio'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de strings
                df['id'] = df['id'].astype(str).str.strip()
                df['anio'] = df['anio'].astype(str).str.strip()

                # Obtener lista de registros existentes (id como clave única)
                existentes = set(MB.objects.values_list('id', flat=True))

                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_registro = row['id']

                    # Verificar si el registro ya existe
                    if id_registro in existentes:
                        omitidos += 1
                        continue

                    try:
                        # Función para convertir valores numéricos de forma segura
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        mb_valor = to_decimal(row['mb'])
                        fc_valor = to_decimal(row['fc'])

                        # Procesar el campo 'anio' y convertirlo a fecha
                        try:
                            if isinstance(row['anio'], pd.Timestamp):  # Caso Timestamp
                                fecha_anio = row['anio'].date()
                            else:
                                fecha_anio = datetime.strptime(str(row['anio']).strip(), "%d-%m-%Y").date()
                        except ValueError:
                            print(f"Fila {index+2}: Error al convertir {row['anio']} en fecha - usando 2000-01-01 por defecto")
                            fecha_anio = datetime(2000, 1, 1).date()

                        # Crear o actualizar el registro en la base de datos
                        obj, created = MB.objects.update_or_create(
                            id=id_registro,
                            defaults={
                                'mb': mb_valor,
                                'fc': fc_valor,
                                'anio': fecha_anio
                            }
                        )

                        if created:
                            print(f'Registro agregado con ID {id_registro}: mb={mb_valor}, fc={fc_valor}, anio={fecha_anio}')
                            nuevos_registros += 1
                        else:
                            print(f'Registro actualizado con ID {id_registro}: mb={mb_valor}, fc={fc_valor}, anio={fecha_anio}')
                            omitidos += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        omitidos += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían o con errores): {omitidos}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo} para MB: {str(e)}')



def cargar_administracion_supervision():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'AdministracionSupervision')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo con tipos de datos específicos
                df = pd.read_excel(ruta_archivo, dtype={
                    'id_categoria': str,
                    'mb_seleccionado': str,
                    'unidad': str
                })
                
                # Validar columnas requeridas
                columnas_requeridas = {
                    'id_categoria', 'unidad', 'precio_unitario_clp', 
                    'total_unitario', 'factor_uso', 'cantidad_u_persona', 
                    'mb_seleccionado'
                }
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de datos
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['unidad'] = df['unidad'].astype(str).str.strip()
                df['mb_seleccionado'] = df['mb_seleccionado'].astype(str).str.strip()
                
                # Obtener registros existentes (clave única: id_categoria + unidad)
                existentes = set(AdministracionSupervision.objects.values_list(
                    'id_categoria__id', 'unidad'
                ))
                
                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0
                errores = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    unidad = row['unidad']
                    
                    # Verificar si el registro ya existe
                    if (id_categoria, unidad) in existentes:
                        omitidos += 1
                        continue
                        
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            errores += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            errores += 1
                            continue

                        # Función para conversión segura a Decimal
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        precio_unitario_clp = to_decimal(row['precio_unitario_clp'])
                        total_unitario = to_decimal(row['total_unitario'])
                        factor_uso = to_decimal(row['factor_uso'])
                        cantidad_u_persona = to_decimal(row['cantidad_u_persona'])

                        # Validar unidad
                        unidad = unidad if unidad else "Sin especificar"

                        # Manejar MB seleccionado
                        mb_seleccionado = None
                        mb_id = row['mb_seleccionado']
                        if mb_id and mb_id != 'nan' and mb_id != 'None':
                            try:
                                mb_seleccionado = MB.objects.get(id=int(float(mb_id)))
                            except (MB.DoesNotExist, ValueError):
                                print(f"Fila {index+2}: MB con ID '{mb_id}' no encontrado - usando None")
                                mb_seleccionado = None

                        # Crear nuevo registro
                        print(f"Creando nuevo registro para categoría {id_categoria} - unidad {unidad}")
                        AdministracionSupervision.objects.create(
                            id_categoria=categoria,
                            unidad=unidad,
                            precio_unitario_clp=precio_unitario_clp,
                            total_unitario=total_unitario,
                            factor_uso=factor_uso,
                            cantidad_u_persona=cantidad_u_persona,
                            mb_seleccionado=mb_seleccionado
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        errores += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")
                print(f" - Registros con errores: {errores}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')



def cargar_personal_indirecto_contratista():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'PersonalIndirectoContratista')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo con tipos de datos específicos
                df = pd.read_excel(ruta_archivo, dtype={
                    'id_categoria': str,
                    'mb_seleccionado': str,
                    'unidad': str,
                    'turno': str
                })
                
                # Validar columnas requeridas
                columnas_requeridas = {
                    'id_categoria', 'unidad', 'hh_mes', 'plazo_mes', 
                    'precio_unitario_clp_hh', 'mb_seleccionado', 'turno'
                }
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de datos
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['unidad'] = df['unidad'].astype(str).str.strip()
                df['mb_seleccionado'] = df['mb_seleccionado'].astype(str).str.strip()
                df['turno'] = df['turno'].astype(str).str.strip()
                
                # Obtener registros existentes (clave única: id_categoria + unidad + turno)
                existentes = set(PersonalIndirectoContratista.objects.values_list(
                    'id_categoria__id', 'unidad', 'turno'
                ))
                
                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0
                errores = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    unidad = row['unidad']
                    turno = row['turno']
                    
                    # Verificar si el registro ya existe
                    if (id_categoria, unidad, turno) in existentes:
                        omitidos += 1
                        continue
                        
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            errores += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            errores += 1
                            continue

                        # Función para conversión segura a Decimal
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        hh_mes = to_decimal(row['hh_mes'])
                        plazo_mes = to_decimal(row['plazo_mes'])
                        precio_unitario_clp_hh = to_decimal(row['precio_unitario_clp_hh'])

                        # Validar campos de texto
                        unidad = unidad if unidad else "Sin especificar"
                        turno = turno if turno else "No especificado"

                        # Manejar MB seleccionado
                        mb_seleccionado = None
                        mb_id = row['mb_seleccionado']
                        if mb_id and mb_id != 'nan' and mb_id != 'None':
                            try:
                                mb_seleccionado = MB.objects.get(id=int(float(mb_id)))
                            except (MB.DoesNotExist, ValueError):
                                print(f"Fila {index+2}: MB con ID '{mb_id}' no encontrado - usando None")
                                mb_seleccionado = None

                        # Crear nuevo registro
                        print(f"Creando nuevo registro para categoría {id_categoria} - unidad {unidad} - turno {turno}")
                        PersonalIndirectoContratista.objects.create(
                            id_categoria=categoria,
                            unidad=unidad,
                            hh_mes=hh_mes,
                            plazo_mes=plazo_mes,
                            precio_unitario_clp_hh=precio_unitario_clp_hh,
                            mb_seleccionado=mb_seleccionado,
                            turno=turno
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        errores += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")
                print(f" - Registros con errores: {errores}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')



def cargar_servicios_apoyo():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'ServiciosApoyo')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo con tipos de datos específicos
                df = pd.read_excel(ruta_archivo, dtype={
                    'id_categoria': str,
                    'unidad': str,
                    'cantidad': float,
                    'hh_totales': float,
                    'tarifas_clp': float,
                    'mb': str
                })

                # Validar columnas requeridas
                columnas_requeridas = {'id_categoria', 'unidad', 'cantidad', 'hh_totales', 'tarifas_clp', 'mb'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de datos
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['unidad'] = df['unidad'].astype(str).str.strip()
                df['mb'] = df['mb'].astype(str).str.strip()

                # Obtener registros existentes
                existentes = set(ServiciosApoyo.objects.values_list(
                    'id_categoria__id', 'unidad', 'mb'
                ))

                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0
                errores = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    unidad = row['unidad']
                    mb_id = row['mb']

                    # Verificar si el registro ya existe
                    if (id_categoria, unidad, mb_id) in existentes:
                        omitidos += 1
                        continue
                    
                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            errores += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            errores += 1
                            continue

                        # Función para conversión segura a Decimal
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        cantidad = to_decimal(row['cantidad'])
                        hh_totales = to_decimal(row['hh_totales'])
                        tarifas_clp = to_decimal(row['tarifas_clp'])

                        # Manejar MB seleccionado
                        mb_obj = None
                        if mb_id and mb_id != 'nan' and mb_id != 'None':
                            try:
                                mb_obj = MB.objects.get(id=int(float(mb_id)))
                            except (MB.DoesNotExist, ValueError):
                                print(f"Fila {index+2}: MB con ID '{mb_id}' no encontrado - usando None")
                                mb_obj = None

                        # Crear nuevo registro
                        print(f"Creando nuevo registro para categoría {id_categoria} - unidad {unidad}")
                        ServiciosApoyo.objects.create(
                            id_categoria=categoria,
                            unidad=unidad,
                            cantidad=cantidad,
                            hh_totales=hh_totales,
                            tarifas_clp=tarifas_clp,
                            mb=mb_obj
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        errores += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")
                print(f" - Registros con errores: {errores}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')





def cargar_otros_adm():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'OtrosADM')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)

            try:
                df = pd.read_excel(ruta_archivo)

                # Verificar que las columnas necesarias estén en el archivo
                columnas_requeridas = {'id_categoria', 'dedicacion', 'meses', 'cantidad', 'turno', 'MB'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo {archivo} debe contener las columnas {columnas_requeridas}')

                for _, row in df.iterrows():
                    try:
                        # Obtener la categoría
                        id_categoria_int = row['id_categoria'] if pd.notna(row['id_categoria']) else None
                        id_categoria = CategoriaNuevo.objects.get(id=id_categoria_int) if id_categoria_int else None
                    except (ValueError, CategoriaNuevo.DoesNotExist):
                        print(f'Categoría con id {row["id_categoria"]} no encontrada o no es válida. Saltando fila...')
                        continue

                    # Convertir valores a Decimal
                    def convertir_a_decimal(valor):
                        try:
                            return Decimal(str(valor)) if pd.notna(valor) else Decimal('0')
                        except Exception:
                            print(f'Error al convertir {valor} a Decimal. Usando 0 por defecto.')
                            return Decimal('0')

                    dedicacion = convertir_a_decimal(row['dedicacion'])
                    meses = int(row['meses']) if pd.notna(row['meses']) else 0
                    cantidad = int(row['cantidad']) if pd.notna(row['cantidad']) else 0
                    turno = row['turno']

                    # Obtener el objeto MB por id
                    mb_seleccionado = None
                    if pd.notna(row['MB']):
                        try:
                            mb_seleccionado_int = int(row['MB'])  # Suponiendo que es un ID
                            mb_seleccionado = MB.objects.get(id=mb_seleccionado_int)  # Buscar MB por ID
                        except (ValueError, MB.DoesNotExist):
                            print(f'MB con id {row["MB"]} no encontrado. Usando None.')
                            mb_seleccionado = None

                    # Crear o actualizar el registro en OtrosADM
                    OtrosADM.objects.get_or_create(
                        id_categoria=id_categoria,
                        dedicacion=dedicacion,
                        meses=meses,
                        cantidad=cantidad,
                        turno=turno,
                        MB=mb_seleccionado,  # Asignar el objeto MB
                    )

                print(f'Archivo {archivo} cargado exitosamente en OtrosADM.')

            except Exception as e:
                print(f'Error al procesar el archivo {archivo} para OtrosADM: {e}')



def cargar_administrativo_financiero():
    directorio_archivos = os.path.join(settings.BASE_DIR, 'uploads', 'AdministrativoFinanciero')

    if not os.path.exists(directorio_archivos):
        print(f'El directorio {directorio_archivos} no existe.')
        return

    for archivo in os.listdir(directorio_archivos):
        if archivo.endswith('.xlsx'):
            ruta_archivo = os.path.join(directorio_archivos, archivo)
            print(f"\nProcesando archivo: {archivo}")

            try:
                # Leer archivo con tipos de datos específicos
                df = pd.read_excel(ruta_archivo, dtype={
                    'id_categoria': str,
                    'unidad': str,
                    'valor': float,
                    'meses': int,
                    'sobre_contrato_base': float,
                    'costo_total': float
                })

                # Validar columnas requeridas
                columnas_requeridas = {'id_categoria', 'unidad', 'valor', 'meses', 'sobre_contrato_base', 'costo_total'}
                if not columnas_requeridas.issubset(df.columns):
                    raise ValueError(f'El archivo debe contener las columnas: {columnas_requeridas}')

                # Preprocesamiento: limpieza de datos
                df['id_categoria'] = df['id_categoria'].astype(str).str.strip()
                df['unidad'] = df['unidad'].astype(str).str.strip()

                # Obtener registros existentes (clave única: id_categoria + unidad)
                existentes = set(AdministrativoFinanciero.objects.values_list(
                    'id_categoria__id', 'unidad'
                ))

                # Contadores para estadísticas
                total_registros = 0
                nuevos_registros = 0
                omitidos = 0
                errores = 0

                for index, row in df.iterrows():
                    total_registros += 1
                    id_categoria = row['id_categoria']
                    unidad = row['unidad']

                    # Verificar si el registro ya existe
                    if (id_categoria, unidad) in existentes:
                        omitidos += 1
                        continue

                    try:
                        # Validar y obtener categoría
                        if not id_categoria:
                            print(f"Fila {index+2}: ID de categoría vacío - omitiendo")
                            errores += 1
                            continue

                        try:
                            categoria = CategoriaNuevo.objects.get(id=id_categoria)
                        except CategoriaNuevo.DoesNotExist:
                            print(f"Fila {index+2}: Categoría con ID '{id_categoria}' no encontrada - omitiendo")
                            errores += 1
                            continue

                        # Función para conversión segura a Decimal
                        def to_decimal(valor, default=Decimal('0')):
                            try:
                                return Decimal(str(valor).replace(',', '.')) if pd.notna(valor) else default
                            except (InvalidOperation, TypeError, ValueError):
                                print(f"Fila {index+2}: Valor inválido '{valor}' - usando {default} por defecto")
                                return default

                        # Convertir valores numéricos
                        valor = to_decimal(row['valor'])
                        sobre_contrato_base = to_decimal(row['sobre_contrato_base'])
                        costo_total = to_decimal(row['costo_total'])
                        meses = int(row['meses']) if pd.notna(row['meses']) else 0

                        # Crear nuevo registro
                        print(f"Creando nuevo registro para categoría {id_categoria} - unidad {unidad}")
                        AdministrativoFinanciero.objects.create(
                            id_categoria=categoria,
                            unidad=unidad,
                            valor=valor,
                            meses=meses,
                            sobre_contrato_base=sobre_contrato_base,
                            costo_total=costo_total,
                        )
                        nuevos_registros += 1

                    except Exception as e:
                        print(f"Error procesando fila {index+2}: {str(e)}")
                        errores += 1
                        continue

                print(f"\nResumen para {archivo}:")
                print(f" - Total registros en archivo: {total_registros}")
                print(f" - Nuevos registros creados: {nuevos_registros}")
                print(f" - Registros omitidos (ya existían): {omitidos}")
                print(f" - Registros con errores: {errores}")

            except Exception as e:
                print(f'\nError al procesar el archivo {archivo}: {str(e)}')
