from django.urls import path
from . import views

urlpatterns = [
    # Esta será la ruta: localhost:8000/inventario/
    path('', views.lista_inventario, name='lista_inventario'),
    # Ruta de detalle: localhost:8000/inventarios/detalle/SKU123/
    path('detalle/<str:sku>/', views.detalle_stock, name='detalle_stock'),
]