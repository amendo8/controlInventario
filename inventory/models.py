
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Inventario(models.Model):
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE, related_name='stocks')
    # Añadimos el serial aquí
    serial = models.CharField(
        max_length=100, 
        unique=True,      # Esto evita que registres dos veces el mismo serial
        null=True, 
        blank=True, 
        verbose_name="Número de Serial"
    )
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE)
    cant_disponible = models.PositiveIntegerField(default=1)
    cant_en_transito = models.PositiveIntegerField(default=0)
    cant_danada_por_recibir = models.PositiveIntegerField(default=0)
    foto_factura = models.ImageField(upload_to='imagen/inventory/%Y/%m/', null=True, blank=True)

    class Meta:
        unique_together = ('parte', 'oficina','serial')  # Esto asegura que no puedas tener dos registros con el mismo SKU, oficina y serial
        

    def save(self, *args, **kwargs):
        # Lógica de negocio: Si tiene serial, la cantidad DEBE ser 1
        if self.serial:
            self.cant_disponible = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.parte.nombre} en {self.oficina.nombre}"

class Abastecimiento(models.Model):
    """Observación 2: Registro de compras e importaciones"""
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE, related_name='compras')
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_compra_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_compra = models.DateField()
    numero_factura = models.CharField(max_length=50, blank=True, null=True)
    formato_importacion = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    """
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            # Actualiza automáticamente el stock disponible
            inv, _ = Inventario.objects.get_or_create(parte=self.parte, oficina=self.oficina)
            inv.cant_disponible += self.cantidad
            inv.save()

        if is_new:
            # Buscamos o creamos el registro de inventario
            inv, _ = Inventario.objects.get_or_create(parte=self.parte, oficina=self.oficina)
            
            # EN LUGAR de sumar directamente, creamos un movimiento de Kardex
            # El Kardex se encargará de actualizar el 'inv.cant_disponible'
            MovimientoKardex.objects.create(
                inventario=inv,
                tipo='ENTRADA',
                cantidad=self.cantidad,
                usuario=None, # Aquí deberías pasar el usuario que registra, si lo tienes disponible
                referencia=f"Abastecimiento: Factura {self.numero_factura or 'S/N'}",
                observaciones="Carga automática desde Abastecimiento")"""
            
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        # Guardamos primero el abastecimiento para tener los datos
        super().save(*args, **kwargs)
        
        if is_new:
            # 1. Buscamos o creamos el registro de Inventario para esa Parte en esa Oficina
            # Es vital que coincidan los campos 'parte' y 'oficina'
            inv, created = Inventario.objects.get_or_create(
                parte=self.parte, 
                oficina=self.oficina
            )
            
            # 2. Creamos el movimiento de Kardex vinculado a ese inventario
            # NOTA: Como el admin no pasa el usuario al modelo fácilmente, 
            # usaremos el primer superusuario o lo dejaremos nulo si tu modelo lo permite.
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()

            MovimientoKardex.objects.create(
                inventario=inv,
                tipo='ENTRADA',
                cantidad=self.cantidad,
                usuario=admin_user, 
                referencia=f"Abastecimiento Fact: {self.numero_factura or 'S/N'}",
                observaciones=f"Carga automática desde módulo de Abastecimiento."
            )   



class AlertaInventario(models.Model):
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE)
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE)
    mensaje = models.TextField()
    nivel = models.CharField(max_length=10, choices=[('INFO','Info'), ('CRITICAL','Crítico')], default='INFO')
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

class MovimientoKardex(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada (Abastecimiento/Compra)'),
        ('SALIDA', 'Salida (Despacho a Técnico)'),
        ('DEVOLUCION', 'Devolución (Retorno al Almacén)'),
        ('AJUSTE', 'Ajuste (Auditoría/Pérdida)'),
    ]

    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    serial = models.CharField(max_length=100, null=True, blank=True, verbose_name="Serial del Ítem")
    cantidad = models.PositiveIntegerField()

    
    # Trazabilidad: ¿Quién autorizó? ¿Qué documento lo respalda?
    usuario = models.ForeignKey('users.User', on_delete=models.PROTECT)
    referencia = models.CharField(max_length=100, help_text="Ej: Factura #001 o Orden de Servicio #50")
    observaciones = models.TextField(blank=True, null=True)
    
    # Estos campos son la esencia del Kardex
    saldo_anterior = models.IntegerField(editable=False)
    saldo_nuevo = models.IntegerField(editable=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Kardex"
        verbose_name_plural = "Kardex: Historial de Movimientos"

    def save(self, *args, **kwargs):
        # 1. Obtenemos el saldo actual antes del movimiento
        self.saldo_anterior = self.inventario.cant_disponible

        # 2. Calculamos el nuevo saldo según el tipo
        if self.tipo in ['ENTRADA', 'DEVOLUCION']:
            self.saldo_nuevo = self.saldo_anterior + self.cantidad
        elif self.tipo == 'SALIDA':
            self.saldo_nuevo = self.saldo_anterior - self.cantidad
        elif self.tipo == 'AJUSTE':
            # En ajustes, la cantidad podría ser enviada como negativa o positiva
            self.saldo_nuevo = self.saldo_anterior + self.cantidad 

        # 3. Actualizamos el saldo en el registro de Inventario principal
        self.inventario.cant_disponible = self.saldo_nuevo
        self.inventario.save()

        super().save(*args, **kwargs)

# Señal para el Punto de Reorden
@receiver(post_save, sender=Inventario)
def verificar_reorden(sender, instance, **kwargs):
    if instance.cant_disponible <= instance.parte.stock_minimo:
        AlertaInventario.objects.get_or_create(
            parte=instance.parte,
            oficina=instance.oficina,
            leida=False,
            defaults={'mensaje': f"Stock crítico en {instance.oficina.nombre}", 'nivel': 'CRITICAL'}
        )