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
    imagen = models.ImageField(upload_to='equipos/', null=True, blank=True)

    def __str__(self):
        return f"{self.linea_negocio.nombre} {self.marca} {self.modelo}"
    
class Parte(models.Model):
    nombre = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    
    # --- CAMPO CLAVE PARA EL KARDEX ---
    # True: Es un activo (Dispensador, Monitor). Se registra 1 a 1 con su serial.
    # False: Es consumible (Tornillos, Correas). Se maneja solo por cantidad.
    tiene_serial = models.BooleanField(
        default=False, 
        verbose_name="¿Es serializada?",
        help_text="Marque si la pieza se controla por serial único (Activo)"
    )
    # ----------------------------------

    stock_minimo = models.PositiveIntegerField(default=5)
    imagen = models.ImageField(upload_to='partes/', null=True, blank=True)
    
    equipos_compatibles = models.ManyToManyField(
        'Equipo', # Usamos string por si Equipo está definido abajo
        related_name="partes",
        blank=True
    )

    def __str__(self):
        # Añadimos una marca visual para saber si es serializada en los selects de Django
        marca = " [S]" if self.tiene_serial else ""
        return f"{self.nombre} [{self.sku}]{marca}"

    def obtener_ultimo_precio(self):
        ultima_compra = self.compras.order_by('-fecha_compra').first()
        if ultima_compra:
            return f"${ultima_compra.precio_compra_unitario} (Factura: {ultima_compra.numero_factura})"
        return "Sin registros"
    
    