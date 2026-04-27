from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'rol', 'oficina', 'telefono', 'foto')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos estilos de Tailwind a todos los campos
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'block w-full px-4 py-3 rounded-xl border-slate-200 focus:border-blue-500 focus:ring-blue-500 text-sm transition-all'
            })
            