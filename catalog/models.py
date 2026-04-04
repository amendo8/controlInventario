from django.db import models

class LineaNegocio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Línea de Negocio"
        verbose_name_plural = "Líneas de Negocio"

    def __str__(self):
        return self.nombre



class Equipo(models.Model):
    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    linea_negocio = models.ForeignKey(LineaNegocio, on_delete=models.PROTECT, related_name='equipos',default=1)

    def __str__(self):
        return f"{self.linea_negocio.nombre} {self.marca} {self.modelo}"
    
class Parte(models.Model):
    nombre = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    stock_minimo = models.PositiveIntegerField(default=5)
    
    # Observación 1: Una parte sirve para muchos equipos
    equipos_compatibles = models.ManyToManyField(
        Equipo, 
        related_name="partes",
        blank=True
    )

    def __str__(self):
        return f"{self.nombre} [{self.sku}]"

    def obtener_ultimo_precio(self):
        # Acceso reverso desde el modelo Abastecimiento
        ultima_compra = self.compras.order_by('-fecha_compra').first()
        if ultima_compra:
            return f"${ultima_compra.precio_compra_unitario} (Factura: {ultima_compra.numero_factura})"
        return "Sin registros"