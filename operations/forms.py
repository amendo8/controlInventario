from django import forms
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
        fields = ['guia_courier', 'empresa']
        widgets = {
            'guia_courier': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Número de guía'}),
            'empresa': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Empresa de courier'}),
        }