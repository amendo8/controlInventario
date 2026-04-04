from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Abastecimiento, Inventario, AlertaInventario

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('parte', 'oficina', 'cant_disponible', 'cant_en_transito')
    list_filter = ('oficina', 'parte')

@admin.register(AlertaInventario)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('parte', 'oficina', 'nivel', 'leida', 'fecha')
    list_editable = ('leida',) # Permite marcar como leída desde la lista


admin.site.register(Abastecimiento)