
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Oficina, Localizacion

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información de Rol', {'fields': ('rol', 'oficina')}),
    )

admin.site.register(Oficina)
admin.site.register(Localizacion)