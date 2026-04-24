
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.

class Inventario(models.Model):
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE, related_name='stocks')
    
    serial = models.CharField(
        max_length=100, 
        unique=False, 
        null=True, 
        blank=True, 
        verbose_name="Número de Serial"
    )
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE)
    cant_disponible = models.IntegerField(default=0, verbose_name="Cantidad en stock") # Cambiado a Integer para permitir cálculos
    cant_en_transito = models.PositiveIntegerField(default=0)
    cant_danada_por_recibir = models.PositiveIntegerField(default=0)
    foto_factura = models.ImageField(upload_to='imagen/inventory/%Y/%m/', blank=True, null=True)
    
    class Meta:
        unique_together = ('parte', 'oficina', 'serial')
    
    @property
    def estado_stock(self):
        if self.cant_disponible <= 0:
            return "AGOTADO"
        if self.cant_disponible <= self.parte.stock_minimo:
            return "CRÍTICO"
        return "OK"

    def __str__(self):
        return f"{self.parte.nombre} ({self.serial or 'Genérico'}) en {self.oficina.nombre}"


# Movimientos de Kardex para el seguimiento detallado de entradas y salidas
# inventory/models.py

class MovimientoKardex(models.Model):
    # tipo de operacion Entrada o Salida de parte
    TIPOS = (('ENTRADA', 'Entrada'),
              ('SALIDA', 'Salida'))
    
    # Estado de la parte, si es operativo, dañada, deseño
    ESTADO_CHOICES = [
        ('OPERATIVO', 'Operativo / Nuevo'),
        ('DAÑADO', 'Dañado / Para Reparar'),
        ('DESECHO', 'Desecho / Scrap'),
    ]
    
    # En lugar de seleccionar un 'Inventario' existente:
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE, null=True)
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE, null=True)
    estado_parte = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='OPERATIVO'
    )
    
    tipo = models.CharField(max_length=10, choices=TIPOS)
    serial = models.CharField(max_length=100, null=True, blank=True)
    cantidad = models.IntegerField(default=1)
    
    # Datos de compra (como se ve en tu imagen)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    numero_factura = models.CharField(max_length=50, null=True, blank=True)
    proveedor = models.CharField(max_length=100, null=True, blank=True)
    
    usuario = models.ForeignKey('users.User', on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100, help_text="Ej: OC-2024, Guía #45")
    observaciones = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    
    # Validaciones personalizadas para asegurar la integridad de los datos según el tipo de parte (serializada o genérica)
    def clean(self):
        """
        Validaciones lógicas antes de guardar en la base de datos.
        """
        super().clean()

        # 1. Normalización del Serial (Limpieza de espacios y mayúsculas)
        if self.serial:
            self.serial = self.serial.strip().upper()

        # 2. Lógica para PARTES CON SERIAL
        if self.parte.tiene_serial:
            # Una pieza con serial es una entidad única: cantidad siempre 1
            if self.cantidad != 1:
                raise ValidationError({
                    'cantidad': f"La parte '{self.parte.nombre}' es serializada. "
                                f"La cantidad en el movimiento debe ser exactamente 1."
                })

            # Si es una ENTRADA, verificamos que el serial no exista ya con stock
            if self.tipo == 'ENTRADA' and self.serial:

                from .models import Inventario
                
                # Buscamos si este serial ya tiene stock activo (> 0) en CUALQUIER oficina
                existe_activo = Inventario.objects.filter(
                    parte=self.parte,
                    serial=self.serial,
                    cant_disponible__gt=0
                ).exists()

                if existe_activo:
                    raise ValidationError({
                        'serial': f"El serial '{self.serial}' ya tiene stock activo en el sistema. "
                                  f"No se puede duplicar la existencia de un activo serializado."
                    })
            
            # --- BLOQUEO DE SALDO NEGATIVO ---
            if self.tipo == 'SALIDA':
                from .models import Inventario
                
                # Buscamos el stock actual en esa oficina para esa parte/serial
                filtro = {
                    'parte': self.parte,
                    'oficina': self.oficina,
                }
                if self.serial:
                    filtro['serial'] = self.serial
                else:
                    filtro['serial__isnull'] = True

                inv_actual = Inventario.objects.filter(**filtro).first()
                stock_disponible = inv_actual.cant_disponible if inv_actual else 0

                if stock_disponible < self.cantidad:
                    # Si no hay stock, lanzamos el error que detiene el guardado
                    error_msg = (
                        f"Saldo insuficiente en {self.oficina.nombre}. "
                        f"Stock disponible: {stock_disponible}. "
                        f"Cantidad solicitada: {self.cantidad}."
                    )
                    raise ValidationError({'cantidad': error_msg})
        
        # 3. Lógica para PARTES GENÉRICAS (Sin Serial)
        else:
            # Si el usuario escribió algo en serial por error, lo limpiamos
            if self.serial:
                self.serial = None
            
            # Validamos que la cantidad sea positiva
            if self.cantidad <= 0:
                raise ValidationError({
                    'cantidad': "La cantidad para partes genéricas debe ser mayor a cero."
                })

    def save(self, *args, **kwargs):
        # Forzamos la ejecución de clean() antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)


# Señal para el Punto de Reorden


########################################################################################

@receiver(post_save, sender=MovimientoKardex)
def actualizar_inventario_desde_kardex(sender, instance, created, **kwargs):
    """
    Sincroniza el saldo de Inventario basándose en los movimientos del Kardex.
    Maneja tanto partes serializadas como genéricas.
    """
    if created:
            from .models import Inventario
            # Ya no usamos instance.inventario, usamos los campos directos del movimiento
            inv, _ = Inventario.objects.get_or_create(
                parte=instance.parte,
                oficina=instance.oficina,
                serial=instance.serial if (instance.parte and instance.parte.tiene_serial) else None
            )

            if instance.tipo == 'ENTRADA':
                inv.cant_disponible += instance.cantidad
            elif instance.tipo == 'SALIDA':
                inv.cant_disponible -= instance.cantidad
            
            inv.save()