from django import forms
from .models import Inventario


#Clase para llamar formulario cargar inventario.
"""
class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['parte', 'serial', 'oficina', 'cant_disponible', 'foto_factura']
        widgets = {
            # Estilo Tailwind para que combine con tu proyecto
            'parte': forms.Select(attrs={'class': 'w-full rounded-2xl border-slate-200 bg-slate-50 font-medium text-sm p-3'}),
            'oficina': forms.Select(attrs={'class': 'w-full rounded-2xl border-slate-200 bg-slate-50 font-medium text-sm p-3'}),
            'serial': forms.TextInput(attrs={'class': 'w-full rounded-2xl border-slate-200 p-3 text-sm',
                                             'placeholder': 'Dejar vacío para repuestos genéricos (correas, engranajes...)'}),
            'cant_disponible': forms.NumberInput(attrs={'class': 'w-full rounded-2xl border-slate-200 p-3 text-sm'}),
            'foto_factura': forms.FileInput(attrs={'class': 'text-xs text-slate-500'}),
        }"""

class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['parte', 'oficina', 'serial', 'cant_disponible', 'foto_factura']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos que el serial no sea obligatorio en el formulario
        self.fields['serial'].required = False
        # Valor por defecto de cantidad para evitar errores
        self.fields['cant_disponible'].initial = 1