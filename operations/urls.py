from django.urls import path
from . import views
from inventory import views as inventory_views

urlpatterns = [
    path('', views.home, name='home'),
    #ath('despacho/', views.despacho, name='despacho'),
    #ath('solicitudes/', views.gestion_solicitudes, name='gestion_solicitudes'),
    #ath('inventarios/', inventory_views.lista_inventario, name='lista_inventario'),
]