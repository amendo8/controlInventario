
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save


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
    cant_disponible = models.IntegerField(default=0) # Cambiado a Integer para permitir cálculos
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


"""""""""
class MovimientoKardex(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada (Abastecimiento/Compra)'),
        ('SALIDA', 'Salida (Despacho a Técnico)'),
        ('DEVOLUCION', 'Devolución (Retorno al Almacén)'),
        ('AJUSTE', 'Ajuste (Auditoría/Pérdida)'),
    ]

    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    usuario = models.ForeignKey('users.User', on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)
    saldo_anterior = models.IntegerField(editable=False)
    saldo_nuevo = models.IntegerField(editable=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Bloqueo de fila para evitar condiciones de carrera
            inv = Inventario.objects.select_for_update().get(id=self.inventario.id)
            
            if inv.serial and self.cantidad != 1:
                raise ValidationError(f"El ítem con serial {inv.serial} solo permite cantidad de 1.")

            self.saldo_anterior = inv.cant_disponible

            if self.tipo in ['ENTRADA', 'DEVOLUCION']:
                self.saldo_nuevo = self.saldo_anterior + self.cantidad
            elif self.tipo == 'SALIDA':
                self.saldo_nuevo = self.saldo_anterior - self.cantidad
            elif self.tipo == 'AJUSTE':
                self.saldo_nuevo = self.saldo_anterior + self.cantidad 

            if self.saldo_nuevo < 0:
                raise ValidationError("Stock insuficiente para realizar esta operación.")

            # Actualizar inventario
            inv.cant_disponible = self.saldo_nuevo
            inv.save()

            

            super().save(*args, **kwargs)

"""


class MovimientoKardex(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Compra / Abastecimiento'),
        ('SALIDA', 'Despacho a Técnico'),
        ('DEVOLUCION', 'Retorno de Parte'),
        ('AJUSTE', 'Ajuste de Inventario'),
    ]

    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    
    # --- CAMPOS HEREDADOS DE ABASTECIMIENTO (Consolidados aquí) ---
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True, null=True)
    proveedor = models.CharField(max_length=100, blank=True, null=True)
    # -------------------------------------------------------------

    usuario = models.ForeignKey('users.User', on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100, help_text="Ej: OC-2024, Guía #45")
    observaciones = models.TextField(blank=True, null=True)
    
    saldo_anterior = models.IntegerField(editable=False)
    saldo_nuevo = models.IntegerField(editable=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            inv = Inventario.objects.select_for_update().get(id=self.inventario.id)
            
            # Validación de serial
            if inv.serial and self.cantidad != 1:
                raise ValidationError(f"El ítem serializado {inv.serial} solo permite cantidad 1.")

            self.saldo_anterior = inv.cant_disponible

            # Cálculo de saldos
            if self.tipo in ['ENTRADA', 'DEVOLUCION']:
                self.saldo_nuevo = self.saldo_anterior + self.cantidad
            elif self.tipo == 'SALIDA':
                self.saldo_nuevo = self.saldo_anterior - self.cantidad
                if self.saldo_nuevo < 0:
                    raise ValidationError("Stock insuficiente.")
            else: # AJUSTE
                self.saldo_nuevo = self.saldo_anterior + self.cantidad

            # Sincronización automática del Inventario
            inv.cant_disponible = self.saldo_nuevo
            inv.save()

            super().save(*args, **kwargs)
# Señal para el Punto de Reorden


########################################################################################

