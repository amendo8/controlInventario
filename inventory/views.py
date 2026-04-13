from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum
from .models import Inventario # Asegúrate de que el nombre de la clase sea este
from .forms import InventarioForm

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
    
    # Tomamos el primero solo para sacar el nombre del producto en el título
    producto = items.first() 

    return render(request, 'inventory/detalle.html', {
        'items': items,
        'producto': producto
    })


# Vista para el API que devuelve el detalle del stock en formato JSON
def api_detalle_stock(request, sku):
    try:
        # 1. Filtramos usando tus campos reales: 'parte__sku'
        items = Inventario.objects.filter(parte__sku=sku).select_related('parte', 'oficina')
        
        if not items.exists():
            return JsonResponse({'error': 'SKU no encontrado'}, status=404)

        parte = items[0].parte
        
        # 2. Construimos la lista con tus nombres de campo: cant_disponible, etc.
        sedes_data = []
        for i in items:
            sedes_data.append({
                'nombre': i.oficina.nombre,
                'disponible': i.cant_disponible,      # Nombre correcto según tu modelo
                'transito': i.cant_en_transito,       # Nombre correcto según tu modelo
                'danado': i.cant_danada_por_recibir   # Nombre correcto según tu modelo
            })

        return JsonResponse({
            'nombre': parte.nombre,
            'sku': parte.sku,
            'sedes': sedes_data
        })
    except Exception as e:
        # Esto te mostrará cualquier otro error si llegara a ocurrir
        return JsonResponse({'error': str(e)}, status=500)

# Cargar inventario desde formulario
def cargar_item(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST, request.FILES)
        
        if form.is_valid():
            nuevo_item = form.save(commit=False)
            
            # CASO 1: REPUESTO CON SERIAL (Ej: Tarjeta Madre)
            if nuevo_item.serial:
                # Forzamos la cantidad a 1, sin importar lo que el usuario haya escrito
                nuevo_item.cant_disponible = 1
                
                # Intentamos guardar. Si el serial ya existe, el modelo dará error por el 'unique=True'
                try:
                    nuevo_item.save()
                    return redirect('inventory_list')
                except Exception as e:
                    form.add_error('serial', 'Este serial ya está registrado en el sistema.')
            
            # CASO 2: REPUESTO GENÉRICO (Ej: Correas, Engranajes)
            else:
                # Buscamos si ya existe un registro GENÉRICO (sin serial) para esta parte y oficina
                existente_generico = Inventario.objects.filter(
                    parte=nuevo_item.parte,
                    oficina=nuevo_item.oficina,
                    serial__isnull=True
                ).first()
                
                if existente_generico:
                    # Sumamos la nueva cantidad al registro que ya teníamos
                    existente_generico.cant_disponible += nuevo_item.cant_disponible
                    existente_generico.save()
                    return redirect('inventory_list')
                else:
                    # Si no existe registro genérico previo, creamos el primero
                    nuevo_item.save()
                    return redirect('inventory_list')
        else:
            # Si el formulario falla (por el unique=True del serial, por ejemplo)
            print(f"Errores: {form.errors}")
            
    else:
        form = InventarioForm()
        
    return render(request, 'inventory/cargar.html', {'form': form})