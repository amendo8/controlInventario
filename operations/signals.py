from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Envio, Solicitud
from inventory.models import MovimientoKardex, Inventario
from django.db import transaction

@receiver(post_save, sender=Envio)
def procesar_inventario_por_envio(sender, instance, created, **kwargs):
    # Esto se ejecuta SIEMPRE que se guarda un Envio
    if created and instance.tipo == 'DESPACHO':
        solicitud = instance.solicitud
        detalles = solicitud.detalles.all()
        
        with transaction.atomic():
            for item in detalles:
                # Buscamos el inventario del supervisor
                inv = Inventario.objects.select_for_update().get(
                    parte=item.parte, 
                    oficina=solicitud.supervisor.oficina
                )
                
                # Creamos el movimiento en el Kardex
                MovimientoKardex.objects.create(
                    inventario=inv,
                    tipo='SALIDA',
                    cantidad=item.cantidad,
                    usuario=solicitud.tecnico,
                    referencia=f"Ticket {solicitud.ticket_crm} - Guía {instance.guia_courier}",
                    observaciones=f"Despacho automático via Signal"
                )
            
            # Actualizamos la solicitud a DESPACHADA
            Solicitud.objects.filter(pk=solicitud.pk).update(estado='DESPACHADA')
            print(f"¡LOGRADO! Kardex actualizado via Signal para {solicitud.ticket_crm}")