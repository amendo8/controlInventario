
from django.contrib import admin
from .models import Parte, Equipo, LineaNegocio

@admin.register(Parte)
class ParteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'stock_minimo')
    search_fields = ('nombre', 'sku')

admin.site.register(Equipo)

admin.site.register(LineaNegocio)