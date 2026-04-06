from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages

from .models import Solicitud, DetalleSolicitud
from .forms import SolicitudForm, DetalleSolicitudForm, DetalleSolicitudFormSet, CambioEstatusForm, EnvioForm
from inventory.models import Inventario
from catalog.models import Parte

# Definir transiciones de estado
ESTADOS_DICT = dict(Solicitud.ESTADOS)
TRANSITIONS = {
    'PENDIENTE': ['APROBADA'],
    'APROBADA': ['DESPACHADA'],
    'DESPACHADA': ['RESUELTO'],
    'RESUELTO': ['CERRADA'],
    'CERRADA': [],
}

# Vista de inicio: muestra logo y formulario de login
def home(request):
    if request.user.is_authenticated:
        return redirect('despacho')
    return render(request, 'operations/home.html')

@login_required
def despacho(request):
    solicitudes = Solicitud.objects.select_related('tecnico', 'tecnico__oficina').prefetch_related('detalles__parte').all().order_by('-fecha_creacion')
    solicitudes_data = []
    ahora = timezone.now()
    pending_parts_map = {}
    for solicitud in solicitudes:
        dias_pendientes = (ahora - solicitud.fecha_creacion).days
        partes = []
        for detalle in solicitud.detalles.all():
            partes.append({
                'nombre': detalle.parte.nombre,
                'cantidad': detalle.cantidad,
            })
            if solicitud.estado != 'CERRADA':
                pending_parts_map[detalle.parte.nombre] = pending_parts_map.get(detalle.parte.nombre, 0) + detalle.cantidad

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

    pending_parts = [
        {'nombre': nombre, 'cantidad': cantidad}
        for nombre, cantidad in sorted(pending_parts_map.items(), key=lambda item: item[1], reverse=True)
    ]

    inventarios = Inventario.objects.select_related('parte', 'oficina').order_by('cant_disponible')[:8]
    inventario_items = [
        {
            'parte': inventario.parte.nombre,
            'oficina': inventario.oficina.nombre,
            'disponible': inventario.cant_disponible,
            'en_transito': inventario.cant_en_transito,
            'danada': inventario.cant_danada_por_recibir,
            'stock_minimo': inventario.parte.stock_minimo,
        }
        for inventario in inventarios
    ]

    return render(request, 'operations/despacho.html', {
        'solicitudes': solicitudes_data,
        'pending_parts': pending_parts,
        'inventory_items': inventario_items,
        'pending_count': len(pending_parts),
        'low_stock_count': sum(1 for item in inventario_items if item['disponible'] <= item['stock_minimo']),
        'total_solicitudes': solicitudes.count(),
    })

@login_required
def gestion_solicitudes(request):
    solicitudes = Solicitud.objects.select_related('tecnico', 'tecnico__oficina').prefetch_related('detalles__parte', 'envios').exclude(estado='CERRADA').order_by('-fecha_creacion')
    partes_disponibles = Parte.objects.all()

    solicitud_form = SolicitudForm()
    detalle_formset = DetalleSolicitudFormSet(queryset=DetalleSolicitud.objects.none())

    if request.method == 'POST':
        if 'add_solicitud' in request.POST:
            solicitud_form = SolicitudForm(request.POST)
            detalle_formset = DetalleSolicitudFormSet(request.POST)
            if solicitud_form.is_valid() and detalle_formset.is_valid():
                solicitud = solicitud_form.save()
                for form in detalle_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        detalle = form.save(commit=False)
                        detalle.solicitud = solicitud
                        detalle.save()
                messages.success(request, 'Solicitud creada exitosamente.')
                return redirect('gestion_solicitudes')
        elif 'change_status' in request.POST:
            solicitud_id = request.POST.get('solicitud_id')
            solicitud = get_object_or_404(Solicitud, id=solicitud_id)
            status_form = CambioEstatusForm(request.POST, instance=solicitud)
            new_estado = request.POST.get('estado')
            envio_form = None
            if new_estado == 'RESUELTO':
                envio_form = EnvioForm(request.POST)
            
            if status_form.is_valid() and (envio_form is None or envio_form.is_valid()):
                status_form.save()
                if envio_form:
                    envio = envio_form.save(commit=False)
                    envio.solicitud = solicitud
                    envio.tipo = 'RETORNO'
                    envio.save()
                messages.success(request, f'Estatus de la solicitud {solicitud.ticket_crm} actualizado.')
                return redirect('gestion_solicitudes')
            else:
                error_msg = f'Error al actualizar el estatus: {status_form.errors}'
                if envio_form and not envio_form.is_valid():
                    error_msg += f' Errores en envío: {envio_form.errors}'
                messages.error(request, error_msg)
        elif 'add_partes' in request.POST:
            solicitud_id = request.POST.get('solicitud_id')
            solicitud = get_object_or_404(Solicitud, id=solicitud_id)
            if solicitud.estado != 'CERRADA':
                parte_form = DetalleSolicitudForm(request.POST)
                if parte_form.is_valid():
                    detalle = parte_form.save(commit=False)
                    detalle.solicitud = solicitud
                    detalle.save()
                    messages.success(request, f'Parte agregada a la solicitud {solicitud.ticket_crm}.')
                    return redirect('gestion_solicitudes')
                else:
                    messages.error(request, 'Error al agregar la parte.')
            else:
                messages.error(request, 'No se pueden agregar partes a una solicitud cerrada.')

    solicitudes_data = []
    for solicitud in solicitudes:
        detalles = [
            {
                'parte': detalle.parte.nombre,
                'cantidad': detalle.cantidad,
            }
            for detalle in solicitud.detalles.all()
        ]
        envios = [
            {
                'tipo': envio.get_tipo_display(),
                'guia_courier': envio.guia_courier,
                'empresa': envio.empresa,
                'fecha_envio': envio.fecha_envio,
            }
            for envio in solicitud.envios.all()
        ]
        fecha_despacho = solicitud.envios.filter(tipo='salida').first()
        if fecha_despacho:
            fecha_despacho = fecha_despacho.fecha_envio
        else:
            fecha_despacho = None
        solicitudes_data.append({
            'id': solicitud.id,
            'ticket': solicitud.ticket_crm,
            'tecnico': solicitud.tecnico.username,
            'ubicacion': solicitud.tecnico.oficina.nombre if solicitud.tecnico.oficina else 'Sin oficina',
            'fecha': solicitud.fecha_creacion,
            'estado': solicitud.get_estado_display(),
            'estado_value': solicitud.estado,
            'detalles': detalles,
            'envios': envios,
            'fecha_despacho': fecha_despacho,
            'next_states': [(state, ESTADOS_DICT[state]) for state in TRANSITIONS[solicitud.estado]],
        })

    return render(request, 'operations/gestion_solicitudes.html', {
        'solicitudes': solicitudes_data,
        'solicitud_form': solicitud_form,
        'detalle_formset': detalle_formset,
        'partes_disponibles': partes_disponibles,
    })

