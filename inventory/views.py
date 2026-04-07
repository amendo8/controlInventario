from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Inventario # Asegúrate de que el nombre de la clase sea este

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

