from django import forms
from .models import ArchivoSubido, ProyectoNuevo, CategoriaNuevo, CostoNuevo, Adquisiciones, MaterialesOtros, EquiposConstruccion, ManoObra, ApuGeneral, ApuEspecifico, EspecificoCategoria, StaffEnami, DatosOtrosEP, DatosEP, Cantidades, ContratoSubcontrato, CotizacionMateriales, IngenieriaDetallesContraparte, GestionPermisos, Dueno, MB, AdministracionSupervision, PersonalIndirectoContratista, ServiciosApoyo, OtrosADM, AdministrativoFinanciero

class ArchivoSubidoForm(forms.ModelForm):
    class Meta:
        model = ArchivoSubido
        fields = ['archivo', 'modelo_destino']

class ProyectoNuevoForm(forms.ModelForm):
    class Meta:
        model = ProyectoNuevo
        fields = ['id','nombre','proyecto_relacionado','porcentaje_utilidades','porcentaje_contingencia']
        widgets = {
            "id": forms.TextInput(attrs={"class": "form-control", "placeholder": "ID"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del Proyecto"}),
            "proyecto_relacionado": forms.TextInput(attrs={"class": "form-control", "placeholder": "Proyecto Relacionado"}),
            "porcentaje_utilidades": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "porcentaje_contingencia": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

class CategoriaNuevoForm(forms.ModelForm):
    class Meta:
        model = CategoriaNuevo
        fields = "__all__"
        exclude = ["total_costo"]
        widgets = {
            "id": forms.TextInput(attrs={"class": "form-control", "placeholder": "ID"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la categoría"}),
            "proyecto": forms.Select(attrs={"class": "form-select"}),
            "id_padre": forms.Select(attrs={"class": "form-select"}),
            "categoria_relacionada": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "nivel": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "final": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class CostoNuevoForm(forms.ModelForm):
    class Meta:
        model = CostoNuevo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = CategoriaNuevo.objects.all()
        self.fields['categoria'].label_from_instance = lambda obj: obj.get_full_name()

class AdquisicionesForm(forms.ModelForm):
    class Meta:
        model = Adquisiciones       
        fields = "__all__"
        exclude = ["flete"]
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "tipo_origen": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tipo de origen"}),
            "tipo_categoria": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tipo de categoría"}),
            "costo_unitario": forms.NumberInput(attrs={"class": "form-control", "min": 0,"placeholder": "Costo unitario"}),
            "crecimiento": forms.NumberInput(attrs={"class": "form-control", "min": 0,"placeholder": "Crecimiento"}),
            
        }

class CantidadesForm(forms.ModelForm):
    class Meta:
        model = Cantidades
        fields = "__all__"
        exclude = ["cantidad_final"]
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad_medida": forms.TextInput(attrs={"class": "form-control","placeholder": "Unidad de Medida"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad"}),
            "fc": forms.NumberInput(attrs={"class": "form-control", "min": 0,"placeholder": "Factor de Crecimiento"}),
            
        }

class MaterialesOtrosForm(forms.ModelForm):
    class Meta:
        model = MaterialesOtros
        fields = "__all__"
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "costo_unidad": forms.NumberInput(attrs={"class": "form-control","min": 0,"placeholder": "Costo de la Unidad"}),
            "crecimiento": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Crecimiento"}),
            
            
        }
        

class EquiposConstruccionForm(forms.ModelForm):
    class Meta:
        model = EquiposConstruccion
        fields = "__all__"
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "horas_maquina_unidad": forms.NumberInput(attrs={"class": "form-control","min": 0,"placeholder": "Horas Maquina Unidad"}),
            "costo_maquina_hora": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Costo Maquina Hora"}),
            
            
        }

class ManoObraForm(forms.ModelForm):
    class Meta:
        model = ManoObra
        fields = "__all__"
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "horas_hombre_unidad": forms.NumberInput(attrs={"class": "form-control","min": 0,"placeholder": "Horas Hombre Unidad"}),
            "fp": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Factor de Progreso"}),
            "costo_hombre_hora": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Costo Hombre Hora"}),
            "rendimiento": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Rendimiento"}),
            "tarifa_usd_hh_equipos": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Tarifa USD HH Equipos"}),
            "tarifas_usd_hh_mod": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Tarifas USD HH Mod"}),
            
            
        }
    
   

class APUGeneralForm(forms.ModelForm):
    class Meta:
        model = ApuGeneral
        fields = "__all__"
        

class APUEspecificoForm(forms.ModelForm):
    class Meta:
        model = ApuEspecifico
        fields = "__all__"

class EspecificoCategoriaForm(forms.ModelForm):
    class Meta:
        model = EspecificoCategoria
        fields = "__all__"
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad": forms.TextInput(attrs={"class": "form-control","placeholder": "Unidad"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad"}),
            "dedicacion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Dedicacion"}),
            "duracion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Duracion"}),
            "costo": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Costo"}),
            
        }

class StaffEnamiForm(forms.ModelForm):
    class Meta:
        model = StaffEnami
        fields = "__all__"
        widgets = {
            
            "nombre": forms.TextInput(attrs={"class": "form-control","placeholder": "Nombre"}),
            "valor": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Valor"}),
            "dotacion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Dotacion"}),
            "duracion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Duracion"}),
            "factor_utilizacion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Factor Utilizacion"}),
            "categoria": forms.Select(attrs={"class": "form-control"}),
        }

class DatosOtrosEPForm(forms.ModelForm):
    class Meta:
        model = DatosOtrosEP
        fields = "__all__"
        exclude = ["gestiones"]
        widgets = {
            "comprador": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Comprador"}),
            "dedicacion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Dedicacion"}),
            "plazo": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Plazo"}),
            "sueldo_pax": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Sueldo Pax"}),
            "viajes": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Viajes"}),
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
        }

class DatosEPForm(forms.ModelForm):
    class Meta:
        model = DatosEP
        fields = "__all__"
        widgets = {
            "id": forms.TextInput(attrs={"class": "form-control","placeholder": "ID"}),
            "hh_profesionales": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Horas Hombre Profesionales"}),
            "precio_hh": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Precio HH"}),
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
        }
        

class CotizacionMaterialesForm(forms.ModelForm):
    class Meta:
        model = CotizacionMateriales
        fields = "__all__"
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "tipo_suministro": forms.TextInput(attrs={"class": "form-control","placeholder": "Tipo de Suministro"}),
            "tipo_moneda": forms.TextInput(attrs={"class": "form-control","placeholder": "Tipo de Moneda"}),
            "pais_entrega": forms.TextInput(attrs={"class": "form-control","placeholder": "Pais de Entrega"}),
            "fecha_cotizacion_referencia": forms.DateInput(attrs={"class": "form-control","type": "date","placeholder": "Fecha de Cotizacion"}),
            "cotizacion_usd": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cotizacion USD"}),
            "cotizacion_clp": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cotizacion CLP"}),
            "factor_correccion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Factor de Correccion"}),
            "moneda_aplicada": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Moneda Aplicada"}),
            "flete_unitario": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Flete Unitario"}),
            "origen_precio": forms.TextInput(attrs={"class": "form-control","placeholder": "Origen Precio"}),
            "cotizacion": forms.TextInput(attrs={"class": "form-control","placeholder": "Cotizacion"}),
            "moneda_origen": forms.TextInput(attrs={"class": "form-control","placeholder": "Moneda Origen"}),
            "tasa_cambio": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Tasa de Cambio"}),
            
        }

class ContratoSubcontratoForm(forms.ModelForm):
    class Meta:
        model = ContratoSubcontrato
        fields = "__all__"
        exclude = ["total_usd_indirectos_contratista","usd_por_unidad","usd_total_subcontrato","costo_contrato_total","costo_contrato_unitario"]
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "costo_laboral_indirecto_usd_hh": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Costo Laboral Indirecto USD HH"}),
            "fc_subcontrato": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "FC Subcontrato"}),
        }
        

class IngenieriaDetallesContraparteForm(forms.ModelForm):
    class Meta:
        model = IngenieriaDetallesContraparte
        fields = "__all__"
        exclude = ["total_usd"]
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control","placeholder": "Nombre"}),
            "UF": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "UF"}),
            "MB": forms.Select(attrs={"class": "form-control"}),
        }

class GestionPermisosForm(forms.ModelForm):
    class Meta:
        model = GestionPermisos
        fields = "__all__"
        exclude = ["HH","total_usd"]
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control","placeholder": "Nombre"}),
            "dedicacion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Dedicacion"}),
            "meses": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Meses"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad"}),
            "HH": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "HH"}),
            "turno": forms.TextInput(attrs={"class": "form-control","placeholder": "Turno"}),
            "MB": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad Dolar por Hora"}),
            
        }
        

class DuenoForm(forms.ModelForm):
    class Meta:
        model = Dueno
        fields = "__all__"
        widgets = {
            
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control","placeholder": "Nombre"}),
            "total_hh": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Total Horas Hombre"}),
            "costo_hh_us": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Costo Horas Hombre USD"}),
            
            
        }
        

class MBForm(forms.ModelForm):
    class Meta:
        model = MB
        fields = "__all__"
        widgets = {
            
            
            "mb": forms.TextInput(attrs={"class": "form-control","placeholder": "MB"}),
            "fc": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Factor de Crecimiento"}),
            "anio": forms.DateInput(attrs={"class": "form-control","type": "date", "placeholder": "Fecha"}),
            "id": forms.TextInput(attrs={"class": "form-control","min": 0, "placeholder": "ID"}),
            
            
        }

class AdministracionSupervisionForm(forms.ModelForm):
    class Meta:
        model = AdministracionSupervision
        fields = "__all__"
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad": forms.TextInput(attrs={"class": "form-control","placeholder": "Unidad"}),
            "precio_unitario_clp": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Precio Unitario CLP"}),
            "total_unitario": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Total Unitario"}),
            "factor_uso": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Factor de Uso"}),
            "cantidad_u_persona": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad por Persona"}),
            "mb_seleccionado": forms.Select(attrs={"class": "form-control"}),
        }
        

class PersonalIndirectoContratistaForm(forms.ModelForm):
    class Meta:
        model = PersonalIndirectoContratista
        fields = "__all__"
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad": forms.TextInput(attrs={"class": "form-control","placeholder": "Unidad"}),
            "hh_mes": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Horas Hombre por Mes"}),
            "plazo_mes": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Plazo Mes"}),
            "precio_unitario_clp_hh": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Precio Unitario CLP HH"}),
            "mb_seleccionado": forms.Select(attrs={"class": "form-control"}),
            "turno": forms.TextInput(attrs={"class": "form-control","placeholder": "Turno"}),
        }

class ServiciosApoyoForm(forms.ModelForm):
    class Meta:
        model = ServiciosApoyo
        fields = "__all__"
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad": forms.TextInput(attrs={"class": "form-control","placeholder": "Unidad"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad"}),
            "hh_totales": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Horas Hombre Totales"}),
            "tarifas_clp": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Tarifas CLP"}),
            "mb": forms.Select(attrs={"class": "form-control"}),
            
        }

class OtrosADMForm(forms.ModelForm):
    class Meta:
        model = OtrosADM
        fields = "__all__"
        exclude = ["HH","total_usd"]
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "dedicacion": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Dedicacion"}),
            "meses": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Meses"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Cantidad"}),
            "turno": forms.TextInput(attrs={"class": "form-control","placeholder": "Turno"}),
            "MB": forms.Select(attrs={"class": "form-control"}),
        }

class AdministrativoFinancieroForm(forms.ModelForm):
    class Meta:
        model = AdministrativoFinanciero
        fields = "__all__"
        widgets = {
            "id_categoria": forms.Select(attrs={"class": "form-control"}),
            "unidad": forms.TextInput(attrs={"class": "form-control","placeholder": "Unidad"}),
            "valor": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Valor"}),
            "meses": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Meses"}),
            "sobre_contrato_base": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Sobre Contrato Base"}),
            "costo_total": forms.NumberInput(attrs={"class": "form-control","min": 0, "placeholder": "Costo Total"}),
        }
