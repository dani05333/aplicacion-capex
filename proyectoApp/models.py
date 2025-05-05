from django.db import models
from django.db.models import Sum, F, DecimalField
from decimal import Decimal 
from django.db import transaction
import uuid
# Create your models here.

class ProyectoNuevo(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=255)
    proyecto_relacionado = models.IntegerField(null=True, blank=True)
    porcentaje_utilidades = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    porcentaje_contingencia = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    costo_total = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'), editable=False)

    def calcular_costo_total(self, save=False):
        """Calcula el costo total sin causar recursión infinita"""
        total = Decimal('0.00')
        
        categorias_generales = self.categorias.filter(id_padre__isnull=True)
        
        for categoria in categorias_generales.only('total_costo'):
            total += categoria.total_costo or Decimal('0.00')
        
        if save:
            # Actualiza directamente en la base de datos sin llamar a save()
            ProyectoNuevo.objects.filter(id=self.id).update(
                costo_total=total
            )
            # Actualiza el valor en la instancia actual
            self.costo_total = total
        
        return total

    def save(self, *args, **kwargs):
        """Guardado seguro sin recursión"""
        skip_recalc = kwargs.pop('skip_cost_recalculation', False)
        if not skip_recalc:
            self.calcular_costo_total(save=True)
        super().save(*args, **kwargs)
    
    def actualizar_costos_categorias(self):
        """Actualiza costos de categorías y luego recalcula el total"""
        for categoria in self.categorias.all():
            categoria.actualizar_total_costo()
        self.calcular_costo_total(save=True)
    
    
    def __str__(self):
        return self.nombre


class CategoriaNuevo(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=255)
    proyecto = models.ForeignKey(ProyectoNuevo, on_delete=models.CASCADE, related_name='categorias')
    id_padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategorias')
    categoria_relacionada = models.CharField(max_length=50, null=True, blank=True)
    nivel = models.PositiveIntegerField(default=1)
    final = models.BooleanField(default=False)
    total_costo = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, null=True, blank=True)

    def delete(self, *args, **kwargs):
        """Sobrescribe delete() para actualizar totales en la categoría al eliminar adquisiciones."""
        categoria_padre = self.id_padre  # Guardar referencia al padre antes de eliminar
        super().delete(*args, **kwargs)  # Eliminar la categoría actual

        if categoria_padre:
            # Recalcular el total de la categoría padre
            categoria_total = Adquisiciones.objects.filter(id_categoria=categoria_padre).aggregate(total=Sum('total'))['total'] or Decimal('0.00')
            categoria_padre.total_costo = categoria_total  # Asignar el nuevo total
            categoria_padre.save()  # Guardar cambios en la categoría padre

            # Actualizar el total de la categoría padre
            categoria_padre.actualizar_total_costo()

    def calcular_costo_asistencia_vendor(self):
        """Calcula el costo de 'Asistencia Técnica del Vendor' y propaga el valor a sus categorías padres."""
        if self.nombre.lower() == "asistencia tecnica del vendor":
            total_adquisiciones = Adquisiciones.objects.filter(
                id_categoria__proyecto=self.proyecto
            ).exclude(id_categoria=self).aggregate(
                total=Sum('total')
            )['total'] or Decimal('0.00')

            costo_asistencia = total_adquisiciones * Decimal('0.05') * Decimal('0.1')

            # Asignar y guardar el nuevo valor
            self.total_costo = costo_asistencia
            self.save(update_fields=['total_costo'])

            # 🔹 Actualizar categorías padre recursivamente
            if self.id_padre:
                self.id_padre.actualizar_total_costo()

            return self.total_costo
        return Decimal('0.00')

    def calcular_costo_ingenieria(self):
        """Si la categoría es 'Ingeniería de Detalles', calcular solo dentro del mismo proyecto."""
        if self.nombre.lower() == "ingenieria de detalles":
            total_hh = DatosEP.objects.filter(
                id_categoria=self, 
                id_categoria__proyecto=self.proyecto
            ).aggregate(
                total=Sum(F('hh_profesionales') * F('precio_hh'))
            )['total'] or Decimal('0.00')

            return total_hh
        return Decimal('0.00')
    
    def calcular_costo_gestion_compras(self):
        """Calcula el costo total de gestión de compras sumando gestiones y viajes."""
        if self.nombre.lower() == "gestion de compras":
            total_gestion_compras = DatosOtrosEP.objects.filter(
                id_categoria=self
            ).aggregate(
                total=Sum(F('gestiones') + F('viajes'))
            )['total'] or Decimal('0.00')

            return total_gestion_compras
        return Decimal('0.00')

    def calcular_costo_contingencia(self, from_child=False):
        if self.nombre.strip().lower() == "contingencia":
            porcentaje = self.proyecto.porcentaje_contingencia

            if porcentaje is not None:
                categorias_raiz = CategoriaNuevo.objects.filter(id_padre__isnull=True, proyecto=self.proyecto)
                total_base = sum(c.total_costo or Decimal('0.00') for c in categorias_raiz if c.id != self.id)

                costo_contingencia = total_base * (porcentaje / Decimal('100'))
                self.total_costo = costo_contingencia
                self.save(update_fields=['total_costo'])

                # ⚠️ Solo actualizar el padre si no venimos de un hijo (para evitar recursión infinita)
                if self.id_padre and not from_child:
                    self.id_padre.actualizar_total_costo(from_child=True)

                return costo_contingencia
        return Decimal('0.00')



    def calcular_costo_utilidades(self, from_child=False):
        """Calcula el costo de utilidades solo si el proyecto tiene porcentaje_utilidades definido."""
        if self.nombre.strip().lower() == "utilidades":
            porcentaje = self.proyecto.porcentaje_utilidades

            if porcentaje is not None:
                categorias_raiz = CategoriaNuevo.objects.filter(id_padre__isnull=True, proyecto=self.proyecto)

                total_base = sum(c.total_costo or Decimal('0.00') for c in categorias_raiz if c.id != self.id)

                costo_utilidades = total_base * (porcentaje / Decimal('100'))

                self.total_costo = costo_utilidades
                self.save(update_fields=['total_costo'])

                #  Evitar llamada recursiva infinita
                if self.id_padre and not from_child:
                    self.id_padre.actualizar_total_costo(from_child=True)

                return costo_utilidades

        return Decimal('0.00')





    def actualizar_total_costo(self, from_child=False):
        total_costo = Decimal('0.00')

        nombre = self.nombre.strip().lower()

        if nombre == "ingenieria de detalles":
            total_costo += self.calcular_costo_ingenieria()

        elif nombre == "gestion de compras":
            total_costo += self.calcular_costo_gestion_compras()

        elif nombre == "contingencia":
            total_costo += self.calcular_costo_contingencia(from_child=from_child)
            return  # 🔁 Evitamos seguir, ya está calculado

        elif nombre == "utilidades":
            total_costo += self.calcular_costo_utilidades(from_child=from_child)
            return  # 🔁 Evitamos seguir, ya está calculado

        elif nombre == "asistencia tecnica del vendor":
            total_costo += self.calcular_costo_asistencia_vendor()
        
        else:      
            # 🔹 Subcategorías
            hijos = self.subcategorias.all()
            total_hijos = sum(h.total_costo or Decimal('0.00') for h in hijos)
            total_costo += total_hijos

        # 🔹 Costos de otras tablas (solo si no es categoría especial)
        if nombre not in ["contingencia", "utilidades"]:
            total_costo += sum([
                Adquisiciones.objects.filter(id_categoria=self).aggregate(total=Sum('total_con_flete'))['total'] or Decimal('0.00'),
                MaterialesOtros.objects.filter(id_categoria=self).aggregate(total=Sum('total_sitio'))['total'] or Decimal('0.00'),
                EquiposConstruccion.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd'))['total'] or Decimal('0.00'),
                ManoObra.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd'))['total'] or Decimal('0.00'),
                EspecificoCategoria.objects.filter(id_categoria=self).aggregate(total=Sum('total'))['total'] or Decimal('0.00'),
                StaffEnami.objects.filter(categoria=self).aggregate(total=Sum('costo_total'))['total'] or Decimal('0.00'),
                DatosEP.objects.filter(id_categoria=self).aggregate(total=Sum('precio_hh'))['total'] or Decimal('0.00'),
                ContratoSubcontrato.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd_indirectos_contratista'))['total'] or Decimal('0.00'),
                IngenieriaDetallesContraparte.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd'))['total'] or Decimal('0.00'),
                GestionPermisos.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd'))['total'] or Decimal('0.00'),
                Dueno.objects.filter(id_categoria=self).aggregate(total=Sum('costo_total'))['total'] or Decimal('0.00'),
                PersonalIndirectoContratista.objects.filter(id_categoria=self).aggregate(total=Sum('costo_total_us'))['total'] or Decimal('0.00'),
                AdministracionSupervision.objects.filter(id_categoria=self).aggregate(total=Sum('costo_total_us'))['total'] or Decimal('0.00'),
                ServiciosApoyo.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd'))['total'] or Decimal('0.00'),
                OtrosADM.objects.filter(id_categoria=self).aggregate(total=Sum('total_usd'))['total'] or Decimal('0.00'),
                AdministrativoFinanciero.objects.filter(id_categoria=self).aggregate(total=Sum('costo_total'))['total'] or Decimal('0.00'),
            ])

        # 🔹 Guardar resultado
        self.total_costo = total_costo
        self.save(update_fields=['total_costo'])

        # 🔁 Propagar hacia arriba solo si no venimos ya de un hijo
        if self.id_padre and not from_child:
            self.id_padre.actualizar_total_costo(from_child=True)

        # 🔹 Si es categoría raíz (no tiene padre), actualizar el proyecto
        if self.id_padre is None and self.proyecto:
            self.proyecto.calcular_costo_total(save=True)

        # 🔁 Recalcular "contingencia" y "utilidades" si no estamos en ellas
        if nombre not in ["contingencia", "utilidades"]:
            categoria_contingencia = CategoriaNuevo.objects.filter(
                nombre__iexact="contingencia", proyecto=self.proyecto
            ).first()
            if categoria_contingencia:
                categoria_contingencia.calcular_costo_contingencia(from_child=True)

            categoria_utilidades = CategoriaNuevo.objects.filter(
                nombre__iexact="utilidades", proyecto=self.proyecto
            ).first()
            if categoria_utilidades:
                categoria_utilidades.calcular_costo_utilidades(from_child=True)


    def __str__(self):
            return f"{self.id} - {self.nombre}"
    

class Adquisiciones(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, null=True, blank=True, on_delete=models.SET_NULL)
    tipo_origen = models.CharField(max_length=50)
    tipo_categoria = models.CharField(max_length=50)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    crecimiento = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Columna de porcentaje de crecimiento
    flete = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Columna de porcentaje de flete
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    total_con_flete = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)  # Columna de porcentaje de flete

    def save(self, *args, **kwargs):
        if self.costo_unitario is None:
            raise ValueError("El campo 'costo_unitario' no puede ser nulo.")
        
        # Obtener cantidad final de la categoría
        cantidad = Cantidades.objects.filter(id_categoria=self.id_categoria).first()
        cantidad_final = Decimal(cantidad.cantidad_final) if cantidad else Decimal('0.00')

        # Obtener flete_unitario desde CotizacionMateriales
        cotizacion = CotizacionMateriales.objects.filter(id_categoria=self.id_categoria).first()
        flete_unitario = Decimal(cotizacion.flete_unitario) if cotizacion else Decimal('0.00')

        # Convertir `costo_unitario` y `crecimiento` a Decimal
        costo_unitario = Decimal(self.costo_unitario)
        crecimiento = Decimal(self.crecimiento)

        # Calcular total con crecimiento
        if crecimiento > Decimal('0.00'):
            self.total = cantidad_final * costo_unitario * (Decimal('1.00') + crecimiento / Decimal('100.00'))
        else:
            self.total = cantidad_final * costo_unitario

        # Calcular flete como porcentaje del total
        self.flete = self.total * (flete_unitario / Decimal('100.00'))

        # Calcular total con flete
        self.total_con_flete = self.total + self.flete

        # Guardar el objeto con los nuevos valores
        super().save(*args, **kwargs)


        # **Calcular el costo de la categoría "Asistencia Técnica del Vendor"**
        categoria_vendor = CategoriaNuevo.objects.filter(
            nombre__iexact="Asistencia Tecnica del Vendor",
            proyecto=self.id_categoria.proyecto
        ).first()
        
        if categoria_vendor:
            categoria_vendor.calcular_costo_asistencia_vendor()

            # **Actualizar sus categorías padre en cascada**
            categoria_actual = categoria_vendor
            while categoria_actual.id_padre and categoria_actual.id_padre.proyecto == categoria_actual.proyecto:
                categoria_actual.id_padre.actualizar_total_costo()
                categoria_actual = categoria_actual.id_padre  # Subir un nivel

        # Actualizar el total_costo de la categoría actual (solo si pertenece al mismo proyecto)
        if self.id_categoria and self.id_categoria.proyecto == self.id_categoria.proyecto:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()
            if self.id_categoria.id_padre and self.id_categoria.id_padre.proyecto == self.id_categoria.proyecto:
                self.id_categoria.id_padre.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior



    def delete(self, *args, **kwargs):
        """Al eliminar, recalcula y actualiza el total en la categoría y sus superiores."""
        categoria = self.id_categoria
        categoria_padre = categoria.id_padre if categoria else None

        # Eliminar la adquisición
        super().delete(*args, **kwargs)

        # 🔹 Recalcular y actualizar la categoría eliminada (solo si pertenece al mismo proyecto)
        if categoria and categoria.proyecto == self.id_categoria.proyecto:
            categoria.actualizar_total_costo()

        # 🔹 Si la categoría tiene una superior, actualizarla también (solo si pertenece al mismo proyecto)
        if categoria_padre and categoria_padre.proyecto == self.id_categoria.proyecto:
            categoria_padre.actualizar_total_costo()

        # 🔹 Actualizar el total_costo de la categoría "Asistencia Técnica del Vendor" si existe (solo si pertenece al mismo proyecto)
        categoria_vendor = CategoriaNuevo.objects.filter(
            nombre__iexact="Asistencia Tecnica del Vendor",
            proyecto=self.id_categoria.proyecto
        ).first()
        if categoria_vendor:
            categoria_vendor.calcular_costo_asistencia_vendor()

    def __str__(self):
        return f"Adquisición en {self.id_categoria.nombre} - Total: {self.total}"
    

class Cantidades(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE, related_name='cantidades')
    unidad_medida = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=15, decimal_places=2)
    fc = models.DecimalField(max_digits=15, decimal_places=2)
    cantidad_final = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.cantidad is None or self.fc is None:
            raise ValueError("Los campos 'cantidad' y 'fc' no pueden ser nulos.")
        
        # Calcular cantidad_final
        self.cantidad_final = self.cantidad + (self.cantidad * (self.fc / 100))
        super().save(*args, **kwargs)

       
        
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Al eliminar, recalcula y actualiza los totales en la categoría y sus superiores."""
        # Guardar referencia a la categoría y su padre antes de eliminar
        categoria = self.id_categoria
        categoria_padre = categoria.id_padre if categoria else None

        # Eliminar la cantidad
        super().delete(*args, **kwargs)

        # 🔹 Recalcular y actualizar la categoría asociada
        if categoria:
            categoria.actualizar_total_costo()

        # 🔹 Si la categoría tiene una superior, actualizarla también
        if categoria_padre:
            categoria_padre.actualizar_total_costo()

        # 🔹 Actualizar las adquisiciones relacionadas con esta categoría
        adquisiciones = Adquisiciones.objects.filter(id_categoria=categoria)
        for adquisicion in adquisiciones:
            adquisicion.save()  # Esto recalculará el total de la adquisición

    def __str__(self):
        return f"Cantidad {self.id} - {self.id_categoria.nombre}"


class MaterialesOtros(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', null=True, blank=True, on_delete=models.SET_NULL)
    costo_unidad = models.DecimalField(max_digits=10, decimal_places=2)
    crecimiento = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Porcentaje
    
    total_usd = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    fletes = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    total_sitio = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        # Obtener la cantidad relacionada con la categoría
        cantidad = Cantidades.objects.filter(id_categoria=self.id_categoria).first()

        # Si no hay cantidad registrada, se asume cantidad_final = 0
        cantidad_final = cantidad.cantidad_final if cantidad else Decimal('0.00')

        # Asegurar que crecimiento no sea nulo
        crecimiento = self.crecimiento if self.crecimiento is not None else Decimal('0.00')

        # Obtener el flete_unitario desde la tabla CotizacionMateriales
        cotizacion_material = CotizacionMateriales.objects.filter(id_categoria=self.id_categoria).first()
        
        # Si no se encuentra la cotización, se asume flete_unitario = 0
        flete_unitario = cotizacion_material.flete_unitario if cotizacion_material else Decimal('0.00')

        # Calcular total_usd basado en crecimiento
        if crecimiento > 0:
            self.total_usd = cantidad_final * self.costo_unidad * (1 + crecimiento / 100)
        else:
            self.total_usd = cantidad_final * self.costo_unidad

        # Calcular fletes como un porcentaje del total_usd
        self.fletes = self.total_usd * (flete_unitario / 100)

        # Calcular total en sitio
        self.total_sitio = self.total_usd + self.fletes

        # Guardar el objeto en la base de datos
        super().save(*args, **kwargs)


        # Llamar a actualizar_total_costo() en la categoría relacionada
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Sobrescribe el método delete para actualizar las cantidades y costos al eliminar un material."""
        cantidad = Cantidades.objects.filter(id_categoria=self.id_categoria).first()

        # 1️⃣ Recalcular la cantidad final en adquisiciones
        if cantidad:
            cantidad.cantidad_final = (
                MaterialesOtros.objects.filter(id_categoria=self.id_categoria)
                .exclude(id=self.id)  # Excluir el registro actual que será eliminado
                .aggregate(total=Sum('costo_unidad'))['total'] or 0
            )
            cantidad.save()

        # 2️⃣ Eliminar el objeto
        super().delete(*args, **kwargs)

        # 3️⃣ Actualizar costos en la categoría
       

            # Llamar a actualizar_total_costo() en la categoría relacionada
        self.id_categoria.actualizar_total_costo()


    def __str__(self):
        """Retorna el nombre de la categoría asociada"""
        return self.id_categoria.nombre


class EquiposConstruccion(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', null=True, blank=True, on_delete=models.SET_NULL)
    horas_maquina_unidad = models.DecimalField(max_digits=10, decimal_places=2)
    costo_maquina_hora = models.DecimalField(max_digits=10, decimal_places=2)
    total_horas_maquina = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    total_usd = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        """Calcula el total y actualiza la categoría correspondiente según la condición de `final`."""
        cantidad = Cantidades.objects.filter(id_categoria=self.id_categoria).first()
        cantidad_final = cantidad.cantidad_final if cantidad else 0

        self.total_horas_maquina = self.horas_maquina_unidad * cantidad_final

        # ✅ Verificar si la categoría es final
        if self.id_categoria and self.id_categoria.final:
            self.total_usd = self.costo_maquina_hora * cantidad_final * self.horas_maquina_unidad  # 🔹 3 columnas cuando es True
        else:
            self.total_usd = self.costo_maquina_hora * cantidad_final  # 🔹 2 columnas cuando es False

        super().save(*args, **kwargs)

        # 🔹 Actualizar la categoría y sus padres
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Al eliminar, actualiza la categoría y todos sus padres."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # ✅ Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # ✅ Eliminar el equipo

        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo
        while categoria_padre:
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Seguir subiendo en la jerarquía

    def __str__(self):
        return f"Equipo en {self.id_categoria.nombre} - Total USD: {self.total_usd}"


class ManoObra(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', null=True, blank=True, on_delete=models.SET_NULL)
    
    horas_hombre_unidad = models.DecimalField(max_digits=10, decimal_places=2)
    fp = models.DecimalField(max_digits=10, decimal_places=2)
    rendimiento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))

    horas_hombre_final = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    cantidad_horas_hombre = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    tarifas_usd_hh_mod = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    costo_hombre_hora = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    total_hh = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    total_usd_mod = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    tarifa_usd_hh_equipos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_usd_equipos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.88'), editable=False)
    total_usd = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # Se ajusta con la nueva lógica

    def save(self, *args, **kwargs):
        """Calcula los valores antes de guardar el objeto."""
        self.horas_hombre_final = self.horas_hombre_unidad * self.fp

        cantidad = Cantidades.objects.filter(id_categoria=self.id_categoria).first()
        cantidad_final = cantidad.cantidad_final if cantidad else Decimal(0)

        self.total_hh = cantidad_final * self.rendimiento * self.fp
        self.cantidad_horas_hombre = self.horas_hombre_final * cantidad_final
        self.total_usd_mod = self.total_hh * self.tarifas_usd_hh_mod
        self.total_usd_equipos = self.total_hh * self.tarifa_usd_hh_equipos

        # Nueva condición para calcular total_usd
        if self.total_usd_mod == 0 and self.total_usd_equipos == 0:
            self.total_usd = cantidad_final * self.horas_hombre_final * self.costo_hombre_hora
        else:
            self.total_usd = self.total_usd_equipos + self.total_usd_mod

        super().save(*args, **kwargs)

        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Sobrescribe delete() para actualizar los costos en la categoría al eliminar un registro de mano de obra."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # ✅ Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # ✅ Eliminar la mano de obra

        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo
        while categoria_padre:
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Seguir subiendo en la jerarquía

    def __str__(self):
        return f"Mano de Obra {self.id} - {self.id_categoria}"


class ApuEspecifico(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', null=True, blank=True, on_delete=models.SET_NULL, related_name="apus_especifico")
    id_apu_general = models.ForeignKey('ApuGeneral', on_delete=models.CASCADE, related_name='apus_especificos')
    id_mano_obra = models.ForeignKey(ManoObra, on_delete=models.CASCADE, related_name='apus_especificos')
    nombre = models.CharField(max_length=255)
    unidad_medida = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    total_usd = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        """Calcula total_usd y actualiza costo_hombre_hora en ManoObra."""
        # Calcular total_usd
        self.total_usd = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)  # Guardar la instancia

        # Si id_apu_general es 1, actualizar costo_hombre_hora en ManoObra
        if self.id_apu_general.id == 5:
            mano_obra = self.id_mano_obra
            mano_obra.actualizar_costo_hombre_hora()

        # Llamar a actualizar_total_costo() en la categoría relacionada
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Sobrescribe delete() para actualizar los costos en la categoría y sus padres al eliminar un registro de ApuEspecifico."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro de ApuEspecifico

        # ✅ Actualizar la categoría principal después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        while categoria_padre:
            categoria_padre.actualizar_total_costo()  # Actualizar el costo en la categoría padre
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return self.nombre
    

class ApuGeneral(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
    

class EspecificoCategoria(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)  
    dedicacion = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de dedicación (0-100)")
    duracion = models.DecimalField(max_digits=5, decimal_places=2, help_text="Duración en meses")
    costo = models.DecimalField(max_digits=10, decimal_places=2, help_text="Costo en dólares al mes")
    total = models.DecimalField(max_digits=15, decimal_places=2, editable=False, default=Decimal('0.00'))  

    def save(self, *args, **kwargs):
        """Recalcula el total y actualiza el total de la categoría."""
        dedicacion_decimal = self.dedicacion / 100  # convertir de entero a decimal
        
        if self.duracion > 0:
            self.total = self.cantidad * self.duracion * dedicacion_decimal * self.costo
        else:
            self.total = self.cantidad * dedicacion_decimal * self.costo

        super().save(*args, **kwargs)


        # Actualizar el total_costo de la categoría
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior    

    def delete(self, *args, **kwargs):
        """Asegurar que al eliminar un registro, se actualice el total en la categoría."""
        categoria = self.id_categoria  # Guardar referencia antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el objeto

        if categoria:
            # Recalcular el total de la categoría sumando todos los `total` restantes
            total_costo = EspecificoCategoria.objects.filter(id_categoria=categoria).aggregate(
                total=Sum('total', output_field=DecimalField())
            )['total'] or Decimal(0)

            # Actualizar el total en la categoría
            categoria.total_costo = total_costo
            categoria.save()

            # Actualizar el total de la categoría padre si existe
            categoria.actualizar_total_costo()
            
    def __str__(self):
        return f"{self.id_categoria.nombre} - ${self.total}"


class StaffEnami(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    dotacion = models.PositiveIntegerField()
    duracion = models.PositiveIntegerField()
    factor_utilizacion = models.DecimalField(max_digits=5, decimal_places=2)
    total_horas_hombre = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    costo_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE, related_name='staff_enami')

    def save(self, *args, **kwargs):
        self.total_horas_hombre = self.duracion * self.factor_utilizacion * Decimal(180)
        self.costo_total = self.valor * self.dotacion * self.total_horas_hombre 
        super().save(*args, **kwargs)

        if self.categoria:
            print(f"Actualizando categoría inmediata: {self.categoria.id}")  # Debugging
            self.categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.categoria:
            categoria_padre = self.categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Actualiza la categoría al eliminar un registro de StaffEnami"""
        categoria = self.categoria  # Guardar referencia antes de eliminar

        super().delete(*args, **kwargs)  # ✅ Eliminar el objeto

        if categoria:
            # ✅ Recalcular el total de costo sumando los `costo_total` restantes
            total_costo = StaffEnami.objects.filter(categoria=categoria).aggregate(
                total=Sum('costo_total', output_field=DecimalField())
            )['total'] or Decimal(0)

            # ✅ Guardar el nuevo total en la categoría
            categoria.total_costo = total_costo
            categoria.save()

    def __str__(self):
        return self.nombre
    

class DatosEP(models.Model):
    id = models.CharField(max_length=50, primary_key=True)  # ID personalizado, no AutoField
    hh_profesionales = models.DecimalField(max_digits=10, decimal_places=2)  # Horas Hombre Profesionales
    precio_hh = models.DecimalField(max_digits=10, decimal_places=2)  # Precio por Hora Hombre
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE, related_name='datos_ep')

    def save(self, *args, **kwargs):
        """Cada vez que se guarde un dato en DatosEP, actualizar la categoría correspondiente."""
        # Calcular el costo antes de guardar
        super().save(*args, **kwargs)  # Guardar la instancia

        # ✅ Si la categoría está definida, actualizar el costo
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Sobrescribe delete() para actualizar los costos en la categoría y sus padres al eliminar un registro de DatosEP."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # ✅ Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # ✅ Eliminar el registro de DatosEP

        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo
        while categoria_padre:
           
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Seguir subiendo en la jerarquía

    def __str__(self):
        return f"{self.id} - {self.id_categoria.nombre}"


class DatosOtrosEP(models.Model):
    id = models.AutoField(primary_key=True)  # ID autoincremental
    comprador = models.IntegerField()
    dedicacion = models.DecimalField(max_digits=10, decimal_places=2)
    plazo = models.DecimalField(max_digits=10, decimal_places=2)
    sueldo_pax = models.DecimalField(max_digits=10, decimal_places=2)
    gestiones = models.DecimalField(max_digits=10, decimal_places=2)
    viajes = models.DecimalField(max_digits=10, decimal_places=2)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE, null=True, related_name='datos_otros_ep')

    def save(self, *args, **kwargs):
        """Cada vez que se guarde un dato en DatosOtrosEP, actualizar la categoría correspondiente."""
        # Guardar la instancia antes de realizar cualquier operación
        self.gestiones = self.comprador * self.plazo * self.sueldo_pax * Decimal(4) * Decimal(160)
        super().save(*args, **kwargs)

        # ✅ Si la categoría está definida, actualizar el costo en la categoría
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizar también las categorías superiores
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()  # Actualizar el costo en la categoría padre
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Sobrescribe delete() para actualizar los costos en la categoría y sus padres al eliminar un registro de DatosOtrosEP."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro de DatosOtrosEP

        # ✅ Actualizar la categoría principal después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        while categoria_padre:
            
            categoria_padre.actualizar_total_costo()  # Actualizar el costo en la categoría padre
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return f"{self.id} - {self.id_categoria.nombre}"


class CotizacionMateriales(models.Model): 
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE)  
    tipo_suministro = models.CharField(max_length=100)
    tipo_moneda = models.CharField(max_length=3)
    pais_entrega = models.CharField(max_length=100)
    fecha_cotizacion_referencia = models.DateField()
    cotizacion_usd = models.DecimalField(max_digits=12, decimal_places=2)
    cotizacion_clp = models.DecimalField(max_digits=12, decimal_places=2)  
    factor_correccion = models.DecimalField(max_digits=5, decimal_places=2)
    moneda_aplicada = models.DecimalField(max_digits=5, decimal_places=2)
    flete_unitario = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Porcentaje
    origen_precio = models.CharField(max_length=100)
    cotizacion = models.CharField(max_length=100)
    moneda_origen = models.CharField(max_length=10)
    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=4)

    def save(self, *args, **kwargs):
        """Cada vez que se guarde un dato en DatosOtrosEP, actualizar la categoría correspondiente."""
        # Guardar la instancia antes de realizar cualquier operación
        super().save(*args, **kwargs)

        # ✅ Si la categoría está definida, actualizar el costo en la categoría
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizar también las categorías superiores
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()  # Actualizar el costo en la categoría padre
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior
    
    def delete(self, *args, **kwargs):
           
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  

        super().delete(*args, **kwargs)  

        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        while categoria_padre:
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre       
    
    def __str__(self):
        return f"{self.tipo_suministro} - {self.pais_entrega} ({self.fecha_cotizacion_referencia})"


class ContratoSubcontrato(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE)
    costo_laboral_indirecto_usd_hh = models.DecimalField(max_digits=12, decimal_places=2)
    total_usd_indirectos_contratista = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    usd_por_unidad = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    fc_subcontrato = models.DecimalField(max_digits=5, decimal_places=2)  # Porcentaje
    usd_total_subcontrato = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    costo_contrato_total = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    costo_contrato_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Obtener valores de otras tablas
        cantidad = Cantidades.objects.filter(id_categoria=self.id_categoria).first()
        mano_obra = ManoObra.objects.filter(id_categoria=self.id_categoria).first()
        materiales_otros = MaterialesOtros.objects.filter(id_categoria=self.id_categoria).first()
        cotizacion = CotizacionMateriales.objects.filter(id_categoria=self.id_categoria).first()  

        # Calcular valores
        self.total_usd_indirectos_contratista = (mano_obra.total_hh if mano_obra else 0) * self.costo_laboral_indirecto_usd_hh
        
        # Solo calcular usd_por_unidad si tipo_suministro es "SUB"
        if cotizacion and cotizacion.tipo_suministro == "SUB":
            self.usd_por_unidad = (cotizacion.moneda_aplicada if cotizacion else 0) * (1 + self.fc_subcontrato / 100)
        else:
            self.usd_por_unidad = 0  # O el valor por defecto que prefieras

        self.usd_total_subcontrato = (cantidad.cantidad_final if cantidad else 0) * self.usd_por_unidad
        self.costo_contrato_total = self.usd_total_subcontrato + self.total_usd_indirectos_contratista + (materiales_otros.total_sitio if materiales_otros else 0) + (mano_obra.total_usd if mano_obra else 0)
        self.costo_contrato_unitario = self.costo_contrato_total / (cantidad.cantidad_final if cantidad and cantidad.cantidad_final > 0 else 1)
        
        super().save(*args, **kwargs)

        # ✅ Si la categoría está definida, actualizar el costo en la categoría
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizar también las categorías superiores
        if self.id_categoria:
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()  # Actualizar el costo en la categoría padre
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Sobrescribe delete() para actualizar los costos en la categoría y sus padres al eliminar un registro de ContratoSubcontrato."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro de ContratoSubcontrato

        # ✅ Actualizar la categoría principal después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Si la categoría tiene un padre, actualizarlo también
        while categoria_padre:
            categoria_padre.actualizar_total_costo()  # Actualizar el costo en la categoría padre
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return f"Contrato {self.id} - Categoría: {self.id_categoria.nombre}"


class IngenieriaDetallesContraparte(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    UF = models.DecimalField(max_digits=10, decimal_places=2)
    MB = models.ForeignKey('MB', on_delete=models.SET_NULL, null=True, blank=True)  # Selección manual de MB
    total_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        """Guarda el modelo y actualiza la categoría padre."""
        self.total_usd = self.UF * self.MB.mb
        super().save(*args, **kwargs)  # Guarda el objeto primero


        # ✅ Actualizar la categoría actual
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return self.nombre


class GestionPermisos(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    dedicacion = models.DecimalField(max_digits=5, decimal_places=2)  # En porcentaje
    meses = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField()
    turno = models.CharField(max_length=50)
    MB = models.ForeignKey('MB', on_delete=models.SET_NULL, null=True, blank=True)  # Selección de MB
    HH = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Se calculará antes de guardar
    total_clp = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Se calculará antes de guardar
    total_usd = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Se calculará antes de guardar

    def save(self, *args, **kwargs):
        self.HH = (self.dedicacion / 100) * self.meses * self.cantidad * 180
        self.total_usd = self.total_clp / self.MB.mb if self.MB else 0
        super().save(*args, **kwargs)

         # ✅ Actualizar la categoría actual
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior


    def __str__(self):
        return f"{self.nombre} - {self.total_usd} USD"
    

class Dueno(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    total_hh = models.DecimalField(max_digits=10, decimal_places=2)
    costo_hh_us = models.DecimalField(max_digits=10, decimal_places=2)
    costo_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.costo_total = self.total_hh * self.costo_hh_us
        super().save(*args, **kwargs)

         # ✅ Actualizar la categoría actual (directa)
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la siguiente categoría superior

                
    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return self.nombre


class MB(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    mb = models.DecimalField(max_digits=15, decimal_places=6)  # Valor de MB
    fc = models.DecimalField(max_digits=15, decimal_places=6)  # Valor de FC
    anio = models.DateField(unique=True)  # Año de referencia

    def save(self, *args, **kwargs):
        """Guarda el modelo sin actualizar categorías inexistentes."""
        super().save(*args, **kwargs)  # Guarda el objeto normalmente
        print(f"Registro MB guardado: {self.id} - Fecha: {self.anio}")  # Debugging

    def delete(self, *args, **kwargs):
        """Elimina el registro sin actualizar categorías inexistentes."""
        print(f"Eliminando MB con id {self.id} - Fecha: {self.anio}")  # Debugging
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"MB: {self.mb}, FC: {self.fc}, Fecha: {self.anio}"
    

class AdministracionSupervision(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', on_delete=models.CASCADE)  # Relación con Categoría
    unidad = models.CharField(max_length=255)
    precio_unitario_clp = models.DecimalField(max_digits=15, decimal_places=2)
    total_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    factor_uso = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_u_persona = models.DecimalField(max_digits=10, decimal_places=2)
    mb_seleccionado = models.ForeignKey('MB', on_delete=models.SET_NULL, null=True, blank=True)  # Selección manual de MB
    costo_total_clp = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    costo_total_us = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    costo_total_mb = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.costo_total_clp = self.precio_unitario_clp * self.total_unitario

        if self.mb_seleccionado:
            self.costo_total_us = self.costo_total_clp / self.mb_seleccionado.mb
            self.costo_total_mb = self.costo_total_us * self.mb_seleccionado.fc
        else:
            self.costo_total_us = 0
            self.costo_total_mb = 0

        super().save(*args, **kwargs)

        # ✅ Actualizar la categoría actual
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return f"Administración y Supervisión - {self.id_categoria} - CLP: {self.costo_total_clp}, US$: {self.costo_total_us}, MB: {self.costo_total_mb}"
    

class PersonalIndirectoContratista(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', on_delete=models.CASCADE)  # Relación con Categoría
    mb_seleccionado = models.ForeignKey('MB', on_delete=models.SET_NULL, null=True, blank=True)  # Selección de MB
    turno = models.CharField(max_length=50)
    unidad = models.CharField(max_length=255)
    hh_mes = models.DecimalField(max_digits=10, decimal_places=2)
    plazo_mes = models.DecimalField(max_digits=10, decimal_places=2)
    total_hh = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    precio_unitario_clp_hh = models.DecimalField(max_digits=15, decimal_places=2)
    tarifa_usd_hh = models.DecimalField(max_digits=15, decimal_places=6, editable=False)
    costo_total_clp = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    costo_total_us = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    costo_total_mb = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_hh = self.plazo_mes * self.hh_mes

        if self.mb_seleccionado:
            mb_value = self.mb_seleccionado.mb
            fc_value = self.mb_seleccionado.fc

            self.tarifa_usd_hh = self.precio_unitario_clp_hh / (mb_value * fc_value)
            self.costo_total_clp = self.precio_unitario_clp_hh * self.plazo_mes * self.hh_mes
            self.costo_total_us = self.costo_total_clp / mb_value
            self.costo_total_mb = self.costo_total_us * fc_value
        else:
            self.tarifa_usd_hh = 0
            self.costo_total_clp = 0
            self.costo_total_us = 0
            self.costo_total_mb = 0

        super().save(*args, **kwargs)

        # ✅ Actualizar la categoría actual
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior
    

class ServiciosApoyo(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.CASCADE)
    unidad = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    hh_totales = models.DecimalField(max_digits=10, decimal_places=2)
    tarifas_clp = models.DecimalField(max_digits=15, decimal_places=2)
    mb = models.ForeignKey('MB', on_delete=models.SET_NULL, null=True, blank=True)  # Selección de MB
    total_usd = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # ✅ Asegurar que `mb` tiene un valor antes de multiplicar
        self.total_usd = self.tarifas_clp / self.mb.mb if self.hh_totales and self.mb else Decimal('0')
        super().save(*args, **kwargs)

        # ✅ Actualizar la categoría actual
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return f"{self.id_categoria} - {self.unidad} - {self.total_usd} USD"
    

class OtrosADM(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaNuevo, on_delete=models.SET_NULL, null=True, blank=True)
    HH = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_clp = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    MB = models.ForeignKey('MB', on_delete=models.SET_NULL, null=True, blank=True)  # Selección de MB
    total_usd = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dedicacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Porcentaje
    meses = models.IntegerField()
    cantidad = models.IntegerField()
    turno = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        # Calculamos HH y Total_USD antes de guardar
        self.HH = (self.dedicacion/100) * self.meses * self.cantidad * 180
        self.total_usd = self.total_clp / self.MB.mb if self.MB else 0
        super().save(*args, **kwargs)

         # ✅ Actualizar la categoría actual
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return f"OtrosADM - {self.id_categoria.nombre if self.id_categoria else 'Sin categoría'}"


class AdministrativoFinanciero(models.Model):
    id = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('CategoriaNuevo', on_delete=models.CASCADE, related_name='administrativo_financiero')
    unidad = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    meses = models.IntegerField()
    sobre_contrato_base = models.DecimalField(max_digits=5, decimal_places=2)
    costo_total = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

         # ✅ Actualizar la categoría actual
        if self.id_categoria:
            print(f"Actualizando categoría inmediata: {self.id_categoria.id}")  # Debugging
            self.id_categoria.actualizar_total_costo()

            # ✅ Recorrer las categorías superiores y actualizar costos
            categoria_padre = self.id_categoria.id_padre
            while categoria_padre:
                print(f"Actualizando categoría padre: {categoria_padre.id}")  # Debugging
                categoria_padre.actualizar_total_costo()
                categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def delete(self, *args, **kwargs):
        """Elimina el registro y actualiza las categorías padre."""
        categoria_padre = self.id_categoria.id_padre if self.id_categoria else None  # Obtener el padre antes de eliminar

        super().delete(*args, **kwargs)  # Eliminar el registro

        # ✅ Actualizar la categoría después de la eliminación
        if self.id_categoria:
            self.id_categoria.actualizar_total_costo()

        # ✅ Recorrer las categorías superiores y actualizar costos
        while categoria_padre:
            print(f"Actualizando categoría padre después de eliminar: {categoria_padre.id}")  # Debugging
            categoria_padre.actualizar_total_costo()
            categoria_padre = categoria_padre.id_padre  # Subir a la categoría superior

    def __str__(self):
        return f"{self.id_categoria.nombre} - {self.unidad} ({self.meses} meses)"


#####ESTE MODELO ES PARA LA FUNCION DE SUBIR ARCHIVOS DESDE LA INTERFAZ DE USUARIO#####

class ArchivoSubido(models.Model):
    archivo = models.FileField(upload_to='uploads/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    modelo_destino = models.CharField(max_length=50, choices=[
        ('ProyectoNuevo', 'Proyecto Nuevo'),
        ('CategoriaNuevo', 'Categoría Nueva'),
        ('Adquisiciones', 'Adquisiciones'),
        ('Cantidades', 'Cantidades'),
        ('MaterialesOtros', 'Materiales Otros'),
        ('EquiposConstruccion', 'Equipos Construcción'),
        ('ManoObra', 'Mano Obra'),
        ('EspecificoCategoria', 'Especifico Categoria'),
        ('ApuEspecifico', 'Apu Especifico'),
        ('ApuGeneral', 'Apu General'),
        ('StaffEnami', 'Staff Enami'),
        ('ContratoSubcontrato', 'Contrato Subcontrato'),
        ('CotizacionMateriales', 'Cotizacion Materiales'),
        ('IngenieriaDetallesContraparte','Ingenieria Detalles Contraparte'),
        ('GestionPermisos','Gestion Permisos'),
        ('Dueno','Dueño'),
        ('MB','MB'),
        ('AdministracionSupervision','Administracion Supervision'),
        ('PersonalIndirectoContratista','Personal Indirecto Contratista'),
        ('ServiciosApoyo','Servicios Apoyo'),
        ('OtrosADM','Otros ADM'),
        ('AdministrativoFinanciero','Administrativo Financiero'),
        ('DatosEP','Datos EP'),
        ('DatosOtrosEP','Datos Otros EP'),
        
        
    ])
    
    def __str__(self):
        return f"{self.archivo.name} - {self.modelo_destino}"






