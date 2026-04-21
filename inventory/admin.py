from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import  Inventario, MovimientoKardex



from django.contrib import admin
from .models import MovimientoKardex

@admin.register(MovimientoKardex)
class MovimientoKardexAdmin(admin.ModelAdmin):
    # Quitamos 'inventario' y ponemos 'parte' y 'oficina'
    list_display = ('fecha', 'parte', 'oficina', 'tipo', 'cantidad', 'serial', 'usuario')
    list_filter = ('tipo', 'oficina', 'parte')
    
    # Organizamos los campos en el formulario para que coincidan con tu imagen
    fields = (
        ('parte', 'oficina'), # Aparecerán en la misma línea
        'tipo',
        'serial',
        'cantidad',
        ('precio_unitario', 'numero_factura', 'proveedor'),
        'usuario',
        'referencia',
        'observaciones',
    )

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('parte',  'serial','oficina', 'cant_disponible')
    readonly_fields = ('parte',
                       'serial',
                       'oficina',
                       'cant_disponible', 
                       'cant_en_transito', 
                       'cant_danada_por_recibir')

   