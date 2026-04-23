from PIL.Image import item
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
        # 1. Guardamos la instancia primero
        super().save(*args, **kwargs)
        
        # 2. Solo disparamos la lógica si el estado cambió a DESPACHADA
        if self.pk:
            # Aquí está el truco: usamos filter().first() en lugar de get() 
            # para evitar que el sistema explote si la instancia vieja no se encuentra
            old_instance = Solicitud.objects.filter(pk=self.pk).first()
            
            if old_instance and old_instance.estado != 'DESPACHADA' and self.estado == 'DESPACHADA':
                # Llamamos al método que acabamos de corregir
                self.procesar_despacho_kardex()
    
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


## Método para procesar movimientos de salida al cambiar el estado a DESPACHADA

class Envio(models.Model):
        TIPOS = (('DESPACHADA', 'Despacho al técnico'), ('RETORNO', 'Retorno al almacén'))
    
        solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='envios')
        tipo = models.CharField(max_length=20, choices=TIPOS)
        guia_courier = models.CharField(max_length=100)
        empresa = models.CharField(max_length=50)
        fecha_envio = models.DateField(null=True, blank=True)
        fecha = models.DateTimeField(auto_now_add=True)
    
        # Añadimos este campo para capturar el serial que viene de vuelta si es necesario
        serial_devuelto = models.CharField(max_length=100, null=True, blank=True, help_text="Serial de la pieza dañada")

        def save(self, *args, **kwargs):
            is_new = self._state.adding
            super().save(*args, **kwargs)
        
            if is_new:
                if self.tipo == 'DESPACHADA':
                    self.procesar_despacho()
                elif self.tipo == 'RETORNO':
                    self.procesar_retorno_completo()

        def procesar_despacho(self):
            """
            Lógica para registrar los movimientos de salida (Caracas) 
            y entrada (Barquisimeto) a través del Kardex.
            """

            with transaction.atomic():
                self.solicitud.refresh_from_db()
                detalles = self.solicitud.detalles.all()
                oficina_origen = self.solicitud.supervisor.oficina
                oficina_destino = self.solicitud.tecnico.oficina

                for item in detalles:
                    # --- 1. REGISTRAMOS SALIDA (ORIGEN) ---
                    # Ya no buscamos inv_origen. El Signal lo gestionará.
                    MovimientoKardex.objects.create(
                        parte=item.parte,
                        oficina=oficina_origen,
                        tipo='SALIDA',
                        cantidad=item.cantidad,
                        usuario=self.solicitud.tecnico,
                        referencia=f"Ticket {self.solicitud.ticket_crm}",
                        observaciones=f"Despacho automático hacia {oficina_destino}"
                    )

                    # --- 2. REGISTRAMOS ENTRADA (DESTINO) ---
                    # El Signal creará el registro de Inventario en el destino si no existe.
                    MovimientoKardex.objects.create(
                        parte=item.parte,
                        oficina=oficina_destino,
                        tipo='ENTRADA',
                        cantidad=item.cantidad,
                        usuario=self.solicitud.tecnico,
                        referencia=f"Ticket {self.solicitud.ticket_crm}",
                        observaciones=f"Entrada automática por recepción de {oficina_origen}"
                    )
                
                # Actualizamos el estado de la solicitud
                self.solicitud.estado = 'DESPACHADA'
                # Usamos update_fields para evitar disparar señales innecesarias de la solicitud si no hace falta
                self.solicitud.save(update_fields=['estado'])

        def procesar_retorno_completo(self):
            """Lógica para procesar la devolución de todas las partes del ticket"""
            from inventory.models import Inventario, MovimientoKardex
            from django.db import transaction

            detalles = self.solicitud.detalles.all()
            oficina_tecnico = self.solicitud.tecnico.oficina
            oficina_supervisor = self.solicitud.supervisor.oficina

            with transaction.atomic():
                for item in detalles:
                    # 1. Determinamos cantidad y serial según el tipo de parte
                    if item.parte.tiene_serial:
                        if not self.serial_devuelto:
                            raise ValueError(f"La parte {item.parte.nombre} requiere un serial para el retorno.")
                        cant_mov = 1
                    else:
                        cant_mov = item.cantidad

                    # 2. SALIDA DEL TÉCNICO (Barquisimeto)
                    inv_tec = Inventario.objects.select_for_update().get(parte=item.parte, oficina=oficina_tecnico)
                    MovimientoKardex.objects.create(
                        inventario=inv_tec,
                        tipo='SALIDA',
                        cantidad=cant_mov,
                        serial=self.serial_devuelto if item.parte.tiene_serial else None,
                        referencia=f"RETORNO-{self.solicitud.ticket_crm}",
                        observaciones=f"Técnico devuelve pieza {'dañada' if item.parte.tiene_serial else 'genérica'}"
                    )

                    # 3. ENTRADA AL SUPERVISOR (Caracas)
                    inv_sup, _ = Inventario.objects.select_for_update().get_or_create(
                        parte=item.parte, oficina=oficina_supervisor, defaults={'cant_disponible': 0}
                    )
                    MovimientoKardex.objects.create(
                        inventario=inv_sup,
                        tipo='ENTRADA',
                        cantidad=cant_mov,
                        serial=self.serial_devuelto if item.parte.tiene_serial else None,
                        referencia=f"RETORNO-{self.solicitud.ticket_crm}",
                        observaciones=f"Almacén recibe pieza dañada/retorno. SN: {self.serial_devuelto}"
                    )
