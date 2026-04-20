from django.db import models, transaction
from django.core.exceptions import ValidationError
from inventory.models import Inventario, MovimientoKardex


# procesar el movimiento de salida al cambiar el estado a DESPACHADA
class Solicitud(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('DESPACHADA', 'Despachada'),
        ('RESUELTO', 'Resuelto (CRM OK)'),
        ('CERRADA', 'Cerrada (Logística OK)'),
    )

    ticket_crm = models.CharField(max_length=50, unique=True)
    tecnico = models.ForeignKey('users.User', on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True) # Para el historial de fechas/comentarios
    supervisor = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_revisadas')


    def __str__(self):
        return f"Ticket {self.ticket_crm} - {self.tecnico.username}"

    def save(self, *args, **kwargs):
        # Guardamos primero para tener el ID de la solicitud y luego procesamos el movimiento de salida si es necesario
        super().save(*args, **kwargs)
        # Solo procesamos el movimiento de salida si el estado cambia a DESPACHADA
        if self.pk:  # Solo si la solicitud ya existe (no es nueva)
            old_instance = Solicitud.objects.get(pk=self.pk)
            if old_instance.estado != 'DESPACHADA' and self.estado == 'DESPACHADA':
                # Aquí podrías agregar lógica adicional si necesitas algo específico al despachar
                self.procesar_salida_inventario()
    
    def procesar_salida_inventario(self):
        """
        Recorre todos los artículos vinculados a este ticket 
        y genera los movimientos de salida en el Kardex.
        """
        # Usa una transaccion atomica para asegurar que todo se procese correctamente
        with transaction.atomic():
            pass
            # Asumiendo que tienes un related_name='articulos' en el modelo que detalla las partes
            articulos_a_despachar = self.detalles.all() 
            
            if not articulos_a_despachar.exists():
                raise ValidationError("No hay artículos cargados en esta solicitud para despachar.")

            for item in articulos_a_despachar:
                # Buscamos el inventario en la oficina que despacha (ej: Almacén Central)
                # Si el ítem es serializado, el 'item' ya debería traer el ID del Inventario específico
                inv = Inventario.objects.select_for_update().get(id=item.inventario.id)
                
                MovimientoKardex.objects.create(
                    inventario=inv,
                    tipo='SALIDA',
                    cantidad=item.cantidad,
                    usuario=self.supervisor or self.tecnico, # Quien autoriza/ejecuta
                    referencia=f"DESPACHO CRM: {self.ticket_crm}",
                    observaciones=f"Salida por operación técnica. Ticket ID: {self.id}"
                )
    
    def clean(self):
        if self.estado == 'CERRADA':
            # Requiere al menos un retorno registrado antes de cerrar la solicitud.
            retornos_registrados = self.envios.filter(tipo='RETORNO').count()
            if retornos_registrados == 0:
                raise ValidationError(
                    "Debe registrar al menos un envío de retorno antes de cerrar la solicitud."
                )



# Aquí es donde permitimos múltiples partes por ticket
class DetalleSolicitud(models.Model):
    """Aquí es donde permitimos múltiples partes por ticket"""
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='detalles')
    parte = models.ForeignKey('catalog.Parte', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.parte.nombre}"


# Este modelo se encarga de registrar los envíos tanto de despacho como de retorno, vinculados a una solicitud específica.
class Envio(models.Model):
    TIPOS = (('DESPACHADA', 'Despacho al técnico'), ('RETORNO', 'Retorno al almacén'))
    
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='envios')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    guia_courier = models.CharField(max_length=100)
    empresa = models.CharField(max_length=50)
    fecha_envio = models.DateField(null=True, blank=True)
    # Si quieres ser muy específico, podrías ligar el envío a un DetalleSolicitud,
    # pero por ahora, lo ligamos a la Solicitud general para facilitar la logística.
    fecha = models.DateTimeField(auto_now_add=True)

    ########################################################################

    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and self.tipo == 'DESPACHADA':
            from inventory.models import Inventario, MovimientoKardex
            from django.db import transaction
            
            with transaction.atomic():
                self.solicitud.refresh_from_db()
                detalles = self.solicitud.detalles.all()
                
                # 1. Almacén de Origen (donde está el Supervisor)
                oficina_origen = self.solicitud.supervisor.oficina
                # 2. Almacén de Destino (donde está el Técnico)
                oficina_destino = self.solicitud.tecnico.oficina

                for item in detalles:
                    # --- OPERACIÓN EN ORIGEN (SALIDA) ---
                    inv_origen = Inventario.objects.select_for_update().get(
                        parte=item.parte, 
                        oficina=oficina_origen
                    )
                    
                    MovimientoKardex.objects.create(
                        inventario=inv_origen,
                        tipo='SALIDA',
                        cantidad=item.cantidad,
                        usuario=self.solicitud.tecnico,
                        referencia=f"Ticket {self.solicitud.ticket_crm}",
                        observaciones=f"Salida de {oficina_origen} hacia {oficina_destino}"
                    )

                    # --- OPERACIÓN EN DESTINO (ENTRADA) ---
                    # Usamos get_or_create por si la pieza nunca ha estado en Barquisimeto
                    inv_destino, _ = Inventario.objects.select_for_update().get_or_create(
                        parte=item.parte,
                        oficina=oficina_destino,
                        defaults={'cant_disponible': 0}
                    )
                    
                    MovimientoKardex.objects.create(
                        inventario=inv_destino,
                        tipo='ENTRADA',
                        cantidad=item.cantidad,
                        usuario=self.solicitud.tecnico,
                        referencia=f"Ticket {self.solicitud.ticket_crm}",
                        observaciones=f"Entrada por despacho desde {oficina_origen}"
                    )
                
                # Actualizamos el estado de la solicitud
                from .models import Solicitud
                Solicitud.objects.filter(pk=self.solicitud_id).update(estado='DESPACHADA')