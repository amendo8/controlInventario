
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Inventario(models.Model):
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE, related_name='stocks')
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE)
    cant_disponible = models.PositiveIntegerField(default=0)
    cant_en_transito = models.PositiveIntegerField(default=0)
    cant_danada_por_recibir = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('parte', 'oficina')

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

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            # Actualiza automáticamente el stock disponible
            inv, _ = Inventario.objects.get_or_create(parte=self.parte, oficina=self.oficina)
            inv.cant_disponible += self.cantidad
            inv.save()



class AlertaInventario(models.Model):
    parte = models.ForeignKey('catalog.Parte', on_delete=models.CASCADE)
    oficina = models.ForeignKey('users.Oficina', on_delete=models.CASCADE)
    mensaje = models.TextField()
    nivel = models.CharField(max_length=10, choices=[('INFO','Info'), ('CRITICAL','Crítico')], default='INFO')
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

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