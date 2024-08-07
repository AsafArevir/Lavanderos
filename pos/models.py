# Librerias importadas
import uuid

# Librerias y modulos de django
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import F

# Tabla productos
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_barras = models.CharField(max_length=100)

# Tabla cliente
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField(max_length=100)
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos}"

# Tabla encargo
class Encargo(models.Model):

    ESTADOS_CHOICES = (
        ('ENCARGO', 'Encargo'),
        ('EN_PROCESO', 'En proceso'),
        ('COMPLETADO', 'Completado'),
    )

    Folio = models.CharField(max_length=30) 
    fecha_encargo = models.DateField(auto_now_add=True,editable=False)
    fecha_entrega = models.DateField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='ENCARGO')
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    adeudo = models.DecimalField(max_digits=10, decimal_places=2)
    ingreso = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    entregado = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)

# Tabla activacion
class Activacion(models.Model):
    LAVADORA_CHOICES = (
        ('Lavadora 1', 'Lavadora 1'),
        ('Lavadora 2', 'Lavadora 2'),
        ('Lavadora 3', 'Lavadora 3'),
        ('Lavadora 4', 'Lavadora 4'),
        ('Lavadora 5', 'Lavadora 5'),
        ('Lavadora 6', 'Lavadora 6'),
        ('Lavadora 7', 'Lavadora 7'),
    )

    MOTIVO_CHOICES = (
        ('encargo', 'Encargo'),
        ('publico', 'Público en general'),
        ('mantenimiento', 'Mantenimiento'),
        ('error', 'Error'),
    )

    lavadora = models.CharField(max_length=20, choices=LAVADORA_CHOICES)
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    encargo = models.ForeignKey(Encargo, on_delete=models.SET_NULL, null=True, blank=True)

# Tabla ventas
class Ventas(models.Model):
    cliente = models.CharField(max_length=100)
    productos = models.CharField(max_length=1000)
    importe_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    
# Tabla control del pago encargo    
class ControlPagoEncargos(models.Model):
    encargo = models.ForeignKey(Encargo, on_delete=models.CASCADE)
    fecha_encargo = models.DateField()
    pago_recibido = models.DecimalField(max_digits=10, decimal_places=2)
    adeudo = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_entregado = models.DateField(null=True, blank=True)
    
# Tabla para el control del sueldo final diario
class SaldoFinalDiario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()