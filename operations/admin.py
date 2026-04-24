from django import forms
from django.contrib import admin
from .models import Solicitud, DetalleSolicitud, Envio
from inventory.models import Inventario

class DetalleSolicitudForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Intentamos obtener la oficina del supervisor de la solicitud actual
        # En los inlines, 'instance' es el DetalleSolicitud
        if self.instance and self.instance.pk:
            parte = self.instance.parte
            oficina = self.instance.solicitud.supervisor.oficina
            
            if parte.tiene_serial:
                # Buscamos seriales con stock > 0 en la oficina del supervisor
                qs = Inventario.objects.filter(
                    parte=parte,
                    oficina=oficina,
                    cant_disponible__gt=0
                ).exclude(serial__isnull=True).exclude(serial='')
                
                # Creamos la lista de opciones
                choices = [('', '--- Seleccione SN ---')]
                choices += [(inv.serial, inv.serial) for inv in qs]
                
                # Transformamos el CharField en un ChoiceField dinámico
                self.fields['serial'] = forms.ChoiceField(choices=choices, required=True)
        else:
            # Para filas nuevas, si no hay parte seleccionada, el campo se queda normal
            # o se puede deshabilitar hasta que se guarde la primera vez.
            self.fields['serial'].widget.attrs['placeholder'] = "Guarde para ver seriales"

class DetalleInline(admin.TabularInline):
    model = DetalleSolicitud
    form = DetalleSolicitudForm  # <--- Vinculamos el formulario aquí
    extra = 1

class EnvioInline(admin.TabularInline):
    model = Envio
    extra = 1
    # Sugerencia: solo mostrar si la solicitud no está entregada
    readonly_fields = ('fecha_envio',) 

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('ticket_crm', 'tecnico', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tecnico')
    search_fields = ('ticket_crm',)
    inlines = [DetalleInline, EnvioInline]