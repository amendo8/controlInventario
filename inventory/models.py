
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
        unique=True, 
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
    TIPOS = (('ENTRADA', 'Entrada'), ('SALIDA', 'Salida'))
    
    # En lugar de seleccionar un 'Inventario' existente:
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE, null=True)
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE, null=True)
    
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

    def save(self, *args, **kwargs):
        # Esta es la lógica mágica:
        from .models import Inventario
        
        # 1. Buscamos o creamos el registro de Inventario (el saldo) automáticamente
        inv, _ = Inventario.objects.get_or_create(
            parte=self.parte,
            oficina=self.oficina,
            serial=self.serial if self.parte.tiene_serial else None
        )
        
        # 2. Actualizamos el saldo del inventario antes de guardar el movimiento
        if self.tipo == 'ENTRADA':
            inv.cant_disponible += self.cantidad
        else:
            inv.cant_disponible -= self.cantidad
        
        inv.save()
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