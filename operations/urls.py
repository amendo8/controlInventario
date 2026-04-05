from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('despacho/', views.despacho, name='despacho'),
    path('solicitudes/', views.gestion_solicitudes, name='gestion_solicitudes'),
]