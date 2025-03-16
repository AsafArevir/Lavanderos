from django.core.management.base import BaseCommand
from pos.models import Producto, Inventario

class Command(BaseCommand):
    help = "Inicializa el inventario para los productos de tipo 'producto'"

    def handle(self, *args, **kwargs):
        productos = Producto.objects.filter(tipo="producto")

        for producto in productos:
            # Verificar si ya existe un registro en inventario para evitar duplicados
            inventario, creado = Inventario.objects.get_or_create(producto=producto, defaults={'cantidad': 0})
            
            if creado:
                self.stdout.write(self.style.SUCCESS(f"Inventario creado para el producto: {producto.nombre}"))
            else:
                self.stdout.write(f"El producto '{producto.nombre}' ya tiene inventario.")

        self.stdout.write(self.style.SUCCESS("Inventario inicializado para todos los productos de tipo 'producto'."))


from pos.models import Producto, Inventario

productos = Producto.objects.filter(tipo="producto")
for producto in productos:
    inventario, creado = Inventario.objects.get_or_create(producto=producto, defaults={'cantidad': 0})
    if creado:
        print(f"Inventario creado para el producto: {producto.nombre}")
    else:
        print(f"El producto '{producto.nombre}' ya tiene inventario.")