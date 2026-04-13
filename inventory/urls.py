from django.urls import path
from . import views

urlpatterns = [
    # Esta será la ruta: localhost:8000/inventario/
    path('', views.lista_inventario, name='lista_inventario'),
    # Ruta de detalle: localhost:8000/inventarios/detalle/SKU123/
    path('api/detalle/<str:sku>/', views.api_detalle_stock, name='api_detalle_stock'),
    path('cargar/', views.cargar_item, name='cargar_inventario'),
   
]