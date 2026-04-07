from django.urls import path
from . import views
from inventory import views as inventory_views

urlpatterns = [
    path('', views.home, name='home'),
    path('despacho/', views.despacho, name='despacho'),
    path('solicitudes/', views.gestion_solicitudes, name='gestion_solicitudes'),
    path('inventarios/', inventory_views.lista_inventario, name='lista_inventario'),
]