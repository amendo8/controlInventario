from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('despacho/', views.despacho, name='despacho'),
]