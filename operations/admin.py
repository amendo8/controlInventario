from django.contrib import admin
from .models import Solicitud, DetalleSolicitud, Envio

class DetalleInline(admin.TabularInline):
    model = DetalleSolicitud
    extra = 1

class EnvioInline(admin.TabularInline):
    model = Envio
    extra = 1

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('ticket_crm', 'tecnico', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'tecnico')
    search_fields = ('ticket_crm',)
    inlines = [DetalleInline, EnvioInline]