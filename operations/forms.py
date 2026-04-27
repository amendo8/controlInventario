from django import forms
from django.utils import timezone
from django.forms import modelformset_factory
from .models import Solicitud, DetalleSolicitud, Envio

class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['ticket_crm', 'tecnico']
        widgets = {
            'ticket_crm': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'tecnico': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

class DetalleSolicitudForm(forms.ModelForm):
    class Meta:
        model = DetalleSolicitud
        fields = ['parte', 'cantidad']
        widgets = {
            'parte': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

DetalleSolicitudFormSet = modelformset_factory(DetalleSolicitud, form=DetalleSolicitudForm, extra=1, can_delete=True)

class CambioEstatusForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

class EnvioForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['guia_courier', 'empresa', 'fecha_envio']
        widgets = {
            'guia_courier': forms.TextInput(attrs={
                'class': 'text-xs border border-slate-200 p-2 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none', 
                'placeholder': 'N° Guía (Zoom/Tealca)'
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'text-xs border border-slate-200 p-2 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none', 
                'placeholder': 'Empresa'
            }),
            'fecha_envio': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'text-xs border border-slate-200 p-2 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super(EnvioForm, self).__init__(*args, **kwargs)
        # Asigna la fecha de hoy por defecto al campo fecha_envio
        self.fields['fecha_envio'].initial = timezone.now().date()

class AprobacionSupervisorForm(forms.Form):
    """Formulario para que el supervisor autorice y comente"""
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Escriba la observación técnica o motivo de aprobación...',
            'rows': '3'
        }),
        required=True,
        label="Observación del Supervisor"
    )
    