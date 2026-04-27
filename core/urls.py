"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    #llama al admin para administrar base de datos
    path('admin/', admin.site.urls),
    
    #Utiliza las utilidades de django para el login, reset contraseña, etc
    path('accounts/', include('django.contrib.auth.urls')),
    
    #Da acceso al Dashboard
    path('', include('operations.urls')),
    
    #Maneja las partes
    path('inventarios/', include('inventory.urls')),
    
    #Maneja los usuarios, creacion, actualización,etc
    path('usuarios/', include('users.urls')),
  
]


# ESTO ES VITAL: Solo añade las rutas de media si estamos en modo DEBUG (desarrollo)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)