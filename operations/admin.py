from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import Solicitud, DetalleSolicitud, Envio, RetornoParte
from catalog.models import Parte



class RetornoParteForm(forms.ModelForm):
    class Meta:
        model = RetornoParte
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importación interna para evitar errores de carga
        from catalog.models import Parte 
        
        # Filtro de Solicitudes
        if 'solicitud' in self.fields:
            self.fields['solicitud'].queryset = Solicitud.objects.all().order_by('-fecha_creacion')
        
        if 'parte' in self.fields:
        # Filtro de Partes
            self.fields['parte'].queryset = Parte.objects.all().order_by('nombre')


class DetalleSolicitudForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- Lógica de Despacho (Corrección) ---
        
        # 1. Identificamos si es una fila NUEVA (sin guardar en DB)
        es_fila_nueva = not self.instance.pk
        
        if es_fila_nueva:
            # Para filas nuevas, cargamos el desplegable filtrado
            try:
                from inventory.models import Inventario
                
                # Buscamos seriales con stock > 0 (asumiendo oficina central por defecto para despacho)
                # NOTA: Aquí podrías refinar el filtro por la oficina del Supervisor si ya está guardada.
                qs = Inventario.objects.filter(
                    cant_disponible__gt=0
                ).exclude(serial__isnull=True).exclude(serial='')
                
                # Creamos las opciones para el desplegable
                choices = [('', '--- Seleccione SN ---')]
                # Añadimos la parte al label para mejor claridad: "Parte [Serial]"
                choices += [(inv.serial, f"{inv.parte.nombre} [{inv.serial}]") for inv in qs]
                
                # Transformamos el CharField en ChoiceField dinámicamente
                self.fields['serial'] = forms.ChoiceField(choices=choices, required=True)
                
            except ImportError:
                # Manejo de error si no se puede importar Inventario
                pass
        
        else:
            # 2. Si la fila YA EXISTE (pk presente), significa que ya fue despachada.
            # En este caso, el campo debe ser de solo lectura (readonly)
            # Esto se maneja mejor en el get_readonly_fields del Inline,
            # pero aquí aseguramos que no se requiera validación de ChoiceField.
            self.fields['serial'].required = False

class DetalleInline(admin.TabularInline):
    model = DetalleSolicitud
    form = DetalleSolicitudForm
    extra = 0 # Evitamos filas vacías innecesarias
    can_delete = False # Protegemos la integridad: lo despachado no se borra
    
    def get_readonly_fields(self, request, obj=None):
        # Si la solicitud ya está 'Entregada' o 'Despachada', todo es solo lectura
        if obj and obj.estado in ['Entregada', 'Despachada']:
            return ['parte', 'cantidad', 'serial']
        return []



@admin.action(description="Confirmar recepción física (Mover a Inventario Dañado)")
def recibir_partes_accion(modeladmin, request, queryset):
    count = 0
    for obj in queryset:
        if obj.estado == 'TRANSITO':
            obj.confirmar_recepcion(request.user)
            count += 1
    modeladmin.message_user(request, f"Se han recibido {count} partes correctamente.")

@admin.register(RetornoParte)
class RetornoParteAdmin(admin.ModelAdmin):
    form = RetornoParteForm # <--- Asignamos el formulario filtrado
    list_display = ('serial_extraido', 'parte', 'get_ticket', 'tecnico', 'estado', 'fecha_registro')
    list_filter = ('estado', 'tecnico')
    search_fields = ('serial_extraido', 'solicitud__ticket_crm')
    actions = [recibir_partes_accion]

    # Método para mostrar el ticket de forma más limpia en la lista
    def get_ticket(self, obj):
        return obj.solicitud.ticket_crm
    get_ticket.short_description = 'Ticket CRM'

    
    def get_readonly_fields(self, request, obj=None):
        # Si el objeto ya existe (obj no es None) y ya fue RECIBIDO
        if obj and obj.estado == 'RECIBIDO':
            # Bloqueamos todos los campos críticos para que no se altere la historia
            return ['solicitud', 'parte', 'serial_extraido', 'tecnico', 'almacenista']
        return super().get_readonly_fields(request, obj)

class EnvioInline(admin.TabularInline):
    model = Envio
    extra = 0
    can_delete = False
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.estado == 'Entregada':
            return ['fecha_envio', 'guia_transporte', 'empresa_envio']
        return []

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('ticket_crm', 'tecnico', 'estado_color', 'fecha_creacion')
    list_filter = ('estado', 'tecnico')
    search_fields = ('ticket_crm',)
    inlines = [DetalleInline, EnvioInline]
    
    # Decorador para dar color al estado en la lista (Opcional, mejora visual)
    def estado_color(self, obj):
        colors = {
            'Pendiente': 'orange',
            'Despachada': 'blue',
            'Entregada': 'green',
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.estado, 'black'),
            obj.get_estado_display()
        )
    estado_color.short_description = 'Estado'

    def get_readonly_fields(self, request, obj=None):
        # Si la solicitud ya se entregó, bloqueamos los campos principales
        if obj and obj.estado == 'Entregada':
            return ['ticket_crm', 'tecnico', 'estado', 'supervisor']
        return []

    def save_model(self, request, obj, form, change):
        # Si el estado cambia a 'Entregada', podrías disparar aquí 
        # automáticamente los movimientos de Kardex de llegada
        super().save_model(request, obj, form, change)