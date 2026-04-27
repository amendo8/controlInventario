from django import forms
from .models import Inventario


#Clase para llamar formulario cargar inventario.

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