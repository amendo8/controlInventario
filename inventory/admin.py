from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Abastecimiento, Inventario, AlertaInventario

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('parte','serial', 'oficina', 'cant_disponible', 'cant_en_transito', 'ver_miniatura')
    list_filter = ('oficina', 'parte','serial')

    # Bloqueamos el campo cantidad en el admin si hay un serial para que nadie lo edite a mano
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.serial:
            return self.readonly_fields + ('cant_disponible',)
        return self.readonly_fields


    # Esto es para que cuando entres a EDITAR, puedas ver la foto grande
    readonly_fields = ('mostrar_foto_grande',)

    # --- FUNCIÓN PARA LA MINIATURA EN LA LISTA ---
    def ver_miniatura(self, obj):
        if obj.foto_factura:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />', obj.foto_factura.url)
        return "No hay foto"
    ver_miniatura.short_description = 'Factura'

    # --- FUNCIÓN PARA VERLA GRANDE AL EDITAR ---
    def mostrar_foto_grande(self, obj):
        if obj.foto_factura:
            return format_html('<img src="{}" style="max-width: 400px; height: auto; border-radius: 8px;" />', obj.foto_factura.url)
        return "Cargue una imagen para ver la vista previa"
    mostrar_foto_grande.short_description = 'Vista previa'


@admin.register(AlertaInventario)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('parte', 'oficina', 'nivel', 'leida', 'fecha')
    list_editable = ('leida',) # Permite marcar como leída desde la lista


admin.site.register(Abastecimiento)