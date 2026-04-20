from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import  Inventario, MovimientoKardex



from django.contrib import admin
from .models import MovimientoKardex

@admin.register(MovimientoKardex)
class MovimientoKardexAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 
        'get_parte', 
        'get_serial', 
        'tipo', 
        'cantidad', 
        'get_ubicacion',  # Veremos dónde ocurre el movimiento
        'get_stock_actual',
        'referencia'
    )
    
    list_filter = ('tipo', 'inventario__oficina', 'fecha')
    search_fields = ('inventario__parte__nombre', 'referencia')

    def get_queryset(self, request):
        # Optimizamos para que la página cargue rápido
        return super().get_queryset(request).select_related('inventario__parte', 'inventario__oficina')

    @admin.display(description='Parte')
    def get_parte(self, obj):
        return obj.inventario.parte.nombre

    @admin.display(description='Serial')
    def get_serial(self, obj):
        # INTENTA ESTO: Si tu campo se llama 'nro_serial' o similar, cámbialo aquí
        # Si no tienes serial en ningún lado, cambia esto por: return "S/S"
        return getattr(obj.inventario, 'serial', "Sin Serial")

    @admin.display(description='Ubicación / Almacén')
    def get_ubicacion(self, obj):
        # Para un despacho, esta es la oficina de ORIGEN
        return obj.inventario.oficina.nombre

    @admin.display(description='Saldo en Oficina')
    def get_stock_actual(self, obj):
        return f"{obj.inventario.cant_disponible} unds"

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('parte', 'oficina', 'serial', 'cant_disponible')
    readonly_fields = ('cant_disponible', 'cant_en_transito', 'cant_danada_por_recibir')

