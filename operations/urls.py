from django.urls import path
from . import views
from inventory import views as inventory_views

urlpatterns = [
    #vista home
    path('', views.home, name='home'),

    # Vista para que el Supervisor vea la lista de pendientes
    path('aprobaciones/', views.lista_por_aprobar, name='lista_por_aprobar'),
    # Acción de procesar la aprobación (recibe el ID de la solicitud)
    path('aprobaciones/procesar/<int:solicitud_id>/', views.aprobar_solicitud, name='aprobar_solicitud'),

    path('despacho/', views.despacho, name='despacho'),
    path('solicitudes/', views.gestion_solicitudes, name='gestion_solicitudes'),
    path('inventarios/', inventory_views.lista_inventario, name='lista_inventario'),
    path('kardex/', views.KardexListView.as_view(), name='kardex_list')
]