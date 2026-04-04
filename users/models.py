from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.



class Localizacion(models.Model):
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    region = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.ciudad} ({self.region})"

class Oficina(models.Model):
    nombre = models.CharField(max_length=100)
    codigo_sucursal = models.CharField(max_length=20, unique=True)
    localizacion = models.ForeignKey(Localizacion, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

class User(AbstractUser):
    # Definimos los roles según tus actores del Diagrama de Secuencia
    TECNICO = 'TECNICO'
    SUPERVISOR = 'SUPERVISOR'
    ALMACENISTA = 'ALMACENISTA'
    ADMIN_PROCURA = 'ADMIN_PROCURA'
    
    ROLE_CHOICES = [
        (TECNICO, 'Técnico'),
        (SUPERVISOR, 'Supervisor'),
        (ALMACENISTA, 'Almacenista'),
        (ADMIN_PROCURA, 'Administrador de Procura'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default=TECNICO)
    # Relacionamos al usuario con su base de operaciones
    oficina = models.ForeignKey('Oficina', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"