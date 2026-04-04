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

    def __str__(self):
        return f"Ticket {self.ticket_crm} - {self.tecnico.username}"

    def clean(self):
        if self.estado == 'CERRADA':
            # Verificamos que CADA parte pedida tenga su correspondiente envío de retorno
            partes_pedidas = self.detalles.count()
            retornos_registrados = self.envios.filter(tipo='RETORNO').count()
            
            if retornos_registrados < partes_pedidas:
                raise ValidationError(
                    f"Faltan retornos. Se pidieron {partes_pedidas} partes, "
                    f"pero solo se han registrado {retornos_registrados} guías de retorno."
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
    # Si quieres ser muy específico, podrías ligar el envío a un DetalleSolicitud,
    # pero por ahora, lo ligamos a la Solicitud general para facilitar la logística.
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and self.tipo == 'RETORNO':
            # Al retornar, actualizamos el stock dañado para TODAS las partes del ticket
            from inventory.models import Inventario
            detalles = self.solicitud.detalles.all()
            for item in detalles:
                inv, _ = Inventario.objects.get_or_create(
                    parte=item.parte, 
                    oficina=self.solicitud.tecnico.oficina
                )
                inv.cant_danada_por_recibir += item.cantidad
                inv.save()