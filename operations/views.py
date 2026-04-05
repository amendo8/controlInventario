from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Solicitud

# Vista de inicio: muestra logo y formulario de login
def home(request):
    if request.user.is_authenticated:
        return redirect('despacho')
    return render(request, 'operations/home.html')

@login_required
def despacho(request):
    solicitudes = Solicitud.objects.select_related('tecnico', 'tecnico__oficina').all().order_by('-fecha_creacion')
    solicitudes_data = []
    ahora = timezone.now()
    for solicitud in solicitudes:
        dias_pendientes = (ahora - solicitud.fecha_creacion).days
        partes = [
            {
                'nombre': detalle.parte.nombre,
                'cantidad': detalle.cantidad,
            }
            for detalle in solicitud.detalles.select_related('parte').all()
        ]
        solicitudes_data.append({
            'ticket': solicitud.ticket_crm,
            'tecnico': solicitud.tecnico.username,
            'rol': solicitud.tecnico.get_rol_display(),
            'ubicacion': solicitud.tecnico.oficina.nombre if solicitud.tecnico.oficina else 'Sin oficina',
            'fecha': solicitud.fecha_creacion,
            'dias_pendientes': dias_pendientes,
            'partes': partes,
            'estado': solicitud.get_estado_display(),
        })

    return render(request, 'operations/despacho.html', {
        'solicitudes': solicitudes_data,
    })

