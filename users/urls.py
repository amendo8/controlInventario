from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('lista/', views.UserListView.as_view(), name='lista_usuarios'),
    path('nuevo/', views.UserCreateView.as_view(), name='crear_usuario'),
    path('editar/<int:pk>/', views.UserUpdateView.as_view(), name='editar_usuario'), # Nueva ruta
]