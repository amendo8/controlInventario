from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from .forms import CustomUserCreationForm

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'usuarios'
    def get_queryset(self):
        # Filtramos para mostrar solo los usuarios activos
        return User.objects.filter(is_active=True).select_related('oficina').order_by('last_name')

class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:lista_usuarios')

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserCreationForm # Reutilizamos el formulario con estilos Tailwind
    template_name = 'users/user_form.html' # Reutilizamos la misma template de creación
    success_url = reverse_lazy('users:lista_usuarios')


