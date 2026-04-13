from django.db import models
from django.core.exceptions import ValidationError

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

    def clean(self):
        if self.estado == 'CERRADA':
            # Requiere al menos un retorno registrado antes de cerrar la solicitud.
            retornos_registrados = self.envios.filter(tipo='RETORNO').count()
            if retornos_registrados == 0:
                raise ValidationError(
                    "Debe registrar al menos un envío de retorno antes de cerrar la solicitud."
                )

class DetalleSolicitud(models.Model):
    """Aquí es donde permitimos múltiples partes por ticket"""
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='detalles')
    parte = models.ForeignKey('catalog.Parte', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.parte.nombre}"

class Envio(models.Model):
    TIPOS = (('DESPACHO', 'Despacho al técnico'), ('RETORNO', 'Retorno al almacén'))
    
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='envios')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    guia_courier = models.CharField(max_length=100)
    empresa = models.CharField(max_length=50)
    fecha_envio = models.DateField(null=True, blank=True)
    # Si quieres ser muy específico, podrías ligar el envío a un DetalleSolicitud,
    # pero por ahora, lo ligamos a la Solicitud general para facilitar la logística.
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            from inventory.models import Inventario, MovimientoKardex
            detalles = self.solicitud.detalles.all()
            
            for item in detalles:
                # Buscamos el stock en la oficina del técnico
                inv, _ = Inventario.objects.get_or_create(
                    parte=item.parte, 
                    oficina=self.solicitud.tecnico.oficina
                )
                
                if self.tipo == 'DESPACHADA':
                    # 1. Creamos el movimiento de Kardex (esto actualiza automáticamente inv.cant_disponible)
                    MovimientoKardex.objects.create(
                        inventario=inv,
                        tipo='SALIDA',
                        cantidad=item.cantidad,
                        usuario=self.solicitud.tecnico, # Podría ser request.user si lo pasas
                        referencia=f"Ticket {self.solicitud.ticket_crm} / Guía {self.guia_courier}",
                        observaciones=f"Despacho vía {self.empresa}"
                    )
                    # 2. Actualizamos el estado de la solicitud
                    self.solicitud.estado = 'DESPACHADA'
                    self.solicitud.save()

                elif self.tipo == 'RETORNO':
                    inv.cant_danada_por_recibir += item.cantidad
                    inv.save()