from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Abastecimiento, Inventario, AlertaInventario, MovimientoKardex


# 1. Definimos la vista "en línea" para los movimientos del Kardex
class MovimientoKardexInline(admin.TabularInline):
    model = MovimientoKardex
    # Importante: El Kardex es un registro histórico, no debe editarse manualmente
    readonly_fields = ('fecha', 'tipo', 'cantidad', 'saldo_anterior', 'saldo_nuevo', 'usuario', 'referencia')
    # Evitamos que se puedan agregar o borrar movimientos directamente desde aquí para proteger la integridad
    
    # ESTO ES LO MÁS IMPORTANTE PARA EVITAR EL ERROR:
    extra = 0             # No muestra filas vacías para "Añadir"
    max_num = 0           # Desactiva la posibilidad de añadir desde aquí
    can_delete = False    # Evita que se borren movimientos
    # Ordenamos para que el movimiento más reciente aparezca arriba
    ordering = ('-fecha',)

    # Evita que el Admin intente crear un objeto vacío al guardar el Inventario
    def has_add_permission(self, request, obj=None):
        return False


#2. Configuramos el Admin de Inventario
@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    
    # Campos que se ven en la lista principal 
    list_display = ('parte','serial', 'oficina', 'cant_disponible', 'cant_en_transito', 'ver_miniatura')
    list_filter = ('oficina', 'parte','serial')
    search_fields = ('parte__nombre', 'serial')
    
    # Aquí es donde ocurre la magia: insertamos la tabla de movimientos
    inlines = [MovimientoKardexInline]

    readonly_fields = ('cant_disponible',)

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


# 3. Configuramos la vista global del Kardex (opcional, para ver todo el historial del sistema)
@admin.register(MovimientoKardex)
class MovimientoKardexAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'inventario', 'tipo', 'cantidad', 'saldo_nuevo', 'usuario', 'referencia')
    list_filter = ('tipo', 'fecha', 'inventario__oficina')
    search_fields = ('inventario__parte__nombre', 'referencia')
    readonly_fields = ('fecha', 'saldo_anterior', 'saldo_nuevo')

@admin.register(AlertaInventario)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('parte', 'oficina', 'nivel', 'leida', 'fecha')
    list_editable = ('leida',) # Permite marcar como leída desde la lista


admin.site.register(Abastecimiento)