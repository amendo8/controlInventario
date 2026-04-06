
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Oficina, Localizacion

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 1. Agregamos tus campos a la lista principal del Admin
    list_display = ('username', 'email', 'rol', 'oficina', 'mostrar_foto', 'is_staff')
    list_filter = ('rol', 'oficina', 'is_staff')

    fieldsets = UserAdmin.fieldsets + (
        ('Información de Rol', {
            'fields': (
                'rol', 
                'oficina')
                }
            ),
        ('Información Adicional', {
            'fields': (
                'direccion', 
                'telefono', 
                'foto', 
                'ver_foto_detalle')
        }),
    )

    readonly_fields = ('ver_foto_detalle',)

   # Método para la miniatura en la lista
    def mostrar_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.foto.url)
        return "Sin foto"
    mostrar_foto.short_description = 'Foto'

    # Método para ver la foto grande en el formulario de edición
    def ver_foto_detalle(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width: 150px; height: 150px; border-radius: 10px; object-fit: cover;" />', obj.foto.url)
        return "No hay foto cargada"
    ver_foto_detalle.short_description = 'Previsualización de Imagen'





admin.site.register(Oficina)
admin.site.register(Localizacion)