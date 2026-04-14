from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum
from .models import Inventario # Asegúrate de que el nombre de la clase sea este
from .forms import InventarioForm
from django.db import IntegrityError


# Create your views here.

def lista_inventario(request):
    # Agrupamos por Parte y Oficina, sumando las cantidades de todos los seriales
    #resumen_inventario = Inventario.objects.values(
     #   'parte__nombre', 
      #  'parte__sku', 
       # 'oficina__nombre'
    items_agrupados = Inventario.objects.values(
        'parte__nombre', 
        'parte__sku', 
        'oficina__nombre'
    ).annotate(
        total_disponible=Sum('cant_disponible'),
        total_transito=Sum('cant_en_transito')
    ).order_by('parte__nombre')

    # Traemos todo el inventario, pero optimizado para no hacer 1000 consultas
    #items = Inventario.objects.select_related('parte', 'oficina').all()
    return render(request, 'inventory/lista.html', {'existencias': items_agrupados})

def detalle_stock(request, sku):
    # Buscamos todos los items que tengan ese SKU
    items = Inventario.objects.filter(parte__sku=sku).select_related('parte', 'oficina')
    
    # 2. Calculamos el total sumado de todas las sedes para este SKU
    totales = items.aggregate(
        total_general=Sum('cant_disponible'),
        total_transito=Sum('cant_en_transito')
    )

    # Tomamos el primero solo para sacar el nombre del producto en el título
    producto = items.first() 

    return render(request, 'inventory/detalle.html', {
        'items': items, # Esta es la lista de seriales
        'producto': producto,
        'total_general': totales['total_general'] or 0,
        'total_transito': totales['total_transito'] or 0,
    })

   


# Vista para el API que devuelve el detalle del stock en formato JSON
def api_detalle_stock(request, sku):
    items = Inventario.objects.filter(parte__sku=sku)
    total_suma = items.aggregate(total=Sum('cant_disponible'))['total'] or 0
    
    lista_sedes = []
    for i in items:
        lista_sedes.append({
            'nombre': i.oficina.nombre,
            'disponible': i.cant_disponible,
            'serial': i.serial, # Enviamos el serial para el modal
            'transito': i.cant_en_transito,
            'danado': 0 # O tu lógica de dañados
        })

    return JsonResponse({
        'nombre': items.first().parte.nombre,
        'total_general': total_suma, # <--- ENVIAR LA SUMA TOTAL
        'sedes': lista_sedes
    })

# Cargar inventario desde formulario


def cargar_item(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST, request.FILES)
        
        # Extraemos datos manualmente para la lógica de decisión
        parte_id = request.POST.get('parte')
        oficina_id = request.POST.get('oficina')
        serial_ingresado = request.POST.get('serial', '').strip()

        # --- LÓGICA PARA REPUESTOS GENÉRICOS (SIN SERIAL) ---
        if not serial_ingresado:
            existente_generico = Inventario.objects.filter(
                parte_id=parte_id,
                oficina_id=oficina_id,
                serial__isnull=True
            ).first()
            
            if existente_generico:
                try:
                    cantidad = int(request.POST.get('cant_disponible', 1))
                    existente_generico.cant_disponible += cantidad
                    # Si subiste una foto nueva, la actualizamos
                    if request.FILES.get('foto_factura'):
                        existente_generico.foto_factura = request.FILES['foto_factura']
                    existente_generico.save()
                    return redirect('lista_inventario')
                except ValueError:
                    pass

        # --- LÓGICA PARA SERIALIZADOS O NUEVOS REGISTROS ---
        if form.is_valid():
            nuevo_item = form.save(commit=False)
            
            # Si tiene serial, la cantidad SIEMPRE debe ser 1
            if nuevo_item.serial:
                nuevo_item.cant_disponible = 1
            
            try:
                nuevo_item.save()
                return redirect('lista_inventario')
            except IntegrityError:
                # Este error salta si el serial ya existe en la base de datos
                form.add_error('serial', 'ERROR CRÍTICO: Este número de serial ya está registrado en el sistema y no puede duplicarse.')
        else:
            # Si hay otros errores (campos vacíos, etc.)
            print(f"Errores en el formulario: {form.errors}")
            
    else:
        form = InventarioForm()
        
    return render(request, 'inventory/cargar.html', {'form': form})