# Librerias e importacion de elementos en django
from django.shortcuts import render
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Producto, Cliente, Encargo, Activacion, Ventas, ControlPagoEncargos, SaldoFinalDiario, lista_precios, PagosEncargos, TurnoCaja, Inventario
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import requests, json
from django.contrib.auth.views import LoginView
from .decorators import superusuario_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db.models import Sum
#from escpos.printer import Usb
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum
from datetime import datetime
from django.utils.timezone import make_aware
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
from django.db import transaction
from django.contrib import messages

# Vista de la muestra la pagina de inicio
@login_required
def inicio(request):
    return render(request, 'inicio.html')

# Vista de la vista para obtener los productos
@login_required
def productos(request):
    productos = Producto.objects.all().order_by('nombre')
    clientes = Cliente.objects.all().order_by('nombre')

    return render(request, 'productos.html', {'productos': productos, 'clientes': clientes})

# Vista para modificar los productos
@csrf_exempt
def modificar_producto(request, producto_id):
    if request.method == 'POST':

        try:
            producto = Producto.objects.get(id=producto_id)
            data = json.loads(request.body)
            producto.nombre = data.get('nombre', producto.nombre)
            producto.precio = data.get('precio', producto.precio)
            producto.codigo_barras = data.get('codigo_barras', producto.codigo_barras)
            producto.tipo = data.get('tipo', producto.tipo)
            producto.save()

            return JsonResponse({'success': True, 'message': 'Producto modificado correctamente'})

        except Producto.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Producto no encontrado'})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


# Vista para obtener los clientes y mostrarlos
@login_required
def clientes(request):
    clientes = Cliente.objects.all()

    return render(request, 'clientes.html', {'clientes': clientes})


# Vista para agregar un cliente
def agregar_cliente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        telefono = request.POST.get('telefono')
        correo = request.POST.get('correo')
        cliente = Cliente(nombre=nombre, apellidos=apellidos, telefono=telefono, correo=correo)
        cliente.save()

        return JsonResponse({'mensaje': 'Cliente agregado correctamente'}, status=201)

    else:
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)

# Vista para eliminar un cliente
def eliminar_cliente(request, cliente_id):
    if request.method == 'POST':
        try:

            cliente = Cliente.objects.get(pk=cliente_id)
            cliente.delete()

            return JsonResponse({'mensaje': 'Cliente eliminado correctamente'})

        except Cliente.DoesNotExist:
            return JsonResponse({'error': 'El cliente no existe'}, status=404)

    else:
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)

# Vista de encargo
@login_required
def encargo(request):
    encargos_encargo = Encargo.objects.all().order_by('-fecha_encargo')[:80]
    encargos_proceso = Encargo.objects.filter(estado='EN_PROCESO').order_by('-fecha_encargo')
    encargos_completado = Encargo.objects.filter(estado='COMPLETADO').order_by('-fecha_encargo')
    encargos_entregados = Encargo.objects.filter(estado='ENTREGADO').order_by('-fecha_encargo')
    encargos_con_pagos = []
    for encargo in encargos_entregados:
        pago = ControlPagoEncargos.objects.filter(encargo=encargo).order_by('-fecha_encargo').first()
        encargos_con_pagos.append({
            'folio': encargo.Folio,
            'cliente': encargo.cliente,
            'fecha_entrega_real': pago.fecha_entregado if pago else None,
            'usuario_entrega': pago.usuario.username if pago else None,
            'costo': encargo.costo,
            'adeudo': encargo.adeudo,
        })

    clientes = Cliente.objects.all().order_by('-nombre')

    context = {
        'encargos_encargo': encargos_encargo,
        'encargos_proceso': encargos_proceso,
        'encargos_completado': encargos_completado,
        'encargos_entregados': encargos_con_pagos,
        'clientes': clientes,
    }

    return render(request, 'encargos.html', context)

# Vista para cambiar el estado del encargo
@csrf_exempt
def cambiar_estado_encargo(request, encargo_id):
    if request.method == 'POST':
        estado = request.POST.get('estado', '')
        nuevo_adeudo = float(request.POST.get('nuevo_adeudo', 0))
        adeudo_original = float(request.POST.get('adeudo_original', 0))

        if estado:

            encargo = get_object_or_404(Encargo, id=encargo_id)
            encargo.estado = 'ENTREGADO'
            encargo.adeudo = nuevo_adeudo
            encargo2 = PagosEncargos(encargoCompleto=encargo, fecha=timezone.now(), pago=adeudo_original)
            encargo2.save()
            encargo.save()

            control_pago_encargo = get_object_or_404(ControlPagoEncargos, encargo=encargo)
            if nuevo_adeudo == 0:
                control_pago_encargo.fecha_entregado = timezone.now()
                control_pago_encargo.usuario = request.user

            control_pago_encargo.save()
            return JsonResponse({'success': True})

        else:
            return JsonResponse({'success': False, 'message': 'Estado no proporcionado'}, status=400)

    elif request.method == 'GET':
        encargo = get_object_or_404(Encargo, id=encargo_id)
        return JsonResponse({'adeudo': encargo.adeudo, 'estado': encargo.estado})

    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

# Vista para guardar un encargo
@csrf_exempt
def guardar_encargo(request):


    if request.method == 'POST':
        # data = json.loads(request.body)
        try:
            folio = request.POST.get('folio')
            fecha_encargo = request.POST.get('fecha_encargo')
            fecha_entrega = request.POST.get('fecha_entrega')
            cliente_id = request.POST.get('cliente_id')
            costo = request.POST.get('costo')
            pagado = request.POST.get('pagadoCheckbox') == 'on'
            anticipo = request.POST.get('anticipo')
            adeudo = request.POST.get('adeudo')
            ingreso = request.POST.get('anticipo')
            observaciones = request.POST.get('observaciones')
            forma_pago = request.POST.get('forma_pago')
            productos_json = request.POST.get('productos', '[]')  # Obtener como string

            # user = request.user

            # cajaAbierta = caja_open(user)

            # if not cajaAbierta:
            #     return JsonResponse({'message': 'No hay caja abierta', 'data': {'error': 'No hay caja abierta', 'status': 400}}, status=400)
            

            try:
                productos = json.loads(productos_json)  # Convertir el string JSON a lista de diccionarios
            except json.JSONDecodeError as e:
                return JsonResponse({'error': f"Error al decodificar JSON de productos: {str(e)}"}, status=400)
            

            # Descontar el stock utilizando la función
            resultado, mensaje = descontar_stock(productos)
            if not resultado:
                return JsonResponse({'error': mensaje}, status=400)



            encargo = Encargo(
                Folio=folio,
                fecha_encargo=timezone.now(),
                fecha_entrega=fecha_entrega,
                cliente_id=cliente_id,
                estado='EN_PROCESO',
                costo=costo,
                adeudo=adeudo,
                ingreso=ingreso,
                usuario=request.user,
                observaciones=observaciones,
                forma_pago=forma_pago,
                productos=productos
            )
            encargo.save()

            # Registro para el control de pagos
            ControlPagoEncargos.objects.create(
                encargo=encargo,
                fecha_encargo=timezone.now(),
                pago_recibido=ingreso,
                adeudo=adeudo,
                forma_pago=forma_pago,
                productos=productos
            )

            return JsonResponse({'message': 'Encargo guardado correctamente', 'data': {'folio': folio, 'fecha_encargo': fecha_encargo, 'fecha_entrega': fecha_entrega, 'cliente_id': cliente_id, 'pagado': pagado, 'anticipo': anticipo, 'adeudo': adeudo, 'costo':costo, 'adeudo':adeudo}, 'id': encargo.id}, status=200)

        except Exception as e:
            print(f"Error al guardar el encargo: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)

# Funcion para el manejo de lavadoras
@login_required
def lavadoras(request):
    activaciones = Activacion.objects.order_by('-fecha')
    encargos = Encargo.objects.filter(estado='EN_PROCESO')

    return render(request, 'lavadoras.html', {'encargos': encargos, 'activaciones': activaciones})

# Funcion para activar una lavadora
def guardar_activacion(request):
    if request.method == 'POST':
        lavadora = request.POST.get('lavadora')
        motivo = request.POST.get('motivo')
        comentario = request.POST.get('comentario')
        encargo_id = request.POST.get('encargo')
        usuario = request.user
        encargo = None

        if encargo_id:
            encargo = Encargo.objects.get(id=encargo_id)
            try:
                encargo2 = Encargo.objects.get(id=encargo_id)
                encargo2.estado = 'COMPLETADO'
                encargo2.save(update_fields=['estado'])  # Solo actualizar el campo 'estado'
            except Encargo.DoesNotExist:
                return JsonResponse({'error': 'Encargo no encontrado'}, status=404)

        activacion = Activacion(
            lavadora=lavadora,
            motivo=motivo,
            comentario=comentario,
            fecha = timezone.now(),
            usuario=usuario,
            encargo=encargo
        )

        activacion.save()
        # ipServer1 = '192.168.0.121'
        # ipServer2 = '192.168.0.122'
        # ipServer3 = '192.168.0.123'
        # portRele = None

        # # Enviar la solicitud HTTP al ESP32
        # if lavadora == 'Lavadora 1':
        #     ipServer = ipServer1
        #     portRele = '1'
        # elif lavadora == 'Lavadora 2':
        #     ipServer = ipServer1
        #     portRele = '2'
        # elif lavadora == 'Lavadora 3':
        #     ipServer = ipServer1
        #     portRele = '3'
        # elif lavadora == 'Lavadora 4':
        #     ipServer = ipServer1
        #     portRele = '4'
        # elif lavadora == 'Lavadora 5':
        #     ipServer = ipServer1
        #     portRele = '5'
        # elif lavadora == 'Lavadora 6':
        #     ipServer = ipServer1
        #     portRele = '6'
        # elif lavadora == 'Lavadora 7':
        #     ipServer = ipServer1
        #     portRele = '7'
        # elif lavadora == 'Lavadora 8':
        #     ipServer = ipServer2
        #     portRele = '1'
        # elif lavadora == 'Lavadora 9':
        #     ipServer = ipServer2
        #     portRele = '2'
        # elif lavadora == 'Lavadora 10':
        #     ipServer = ipServer2
        #     portRele = '3'
        # elif lavadora == 'Secadora 1':
        #     ipServer = ipServer3
        #     portRele = '1'
        # elif lavadora == 'Secadora 2':
        #     ipServer = ipServer3
        #     portRele = '2'
        # elif lavadora == 'Secadora 3':
        #     ipServer = ipServer3
        #     portRele = '3'
        # elif lavadora == 'Secadora 4':
        #     ipServer = ipServer3
        #     portRele = '4'
        # elif lavadora == 'Secadora 5':
        #     ipServer = ipServer3
        #     portRele = '5'
        # elif lavadora == 'Secadora 6':
        #     ipServer = ipServer3
        #     portRele = '6'
        # """Añadir más condiciones para las otras lavadoras si es necesario"""
        # Mapeo de lavadoras/secadoras a servidores y puertos
        # ip1= '192.168.101.120'
        # Toluca
        # ip1 = '192.168.0.121'
        # ip2 = '192.168.0.122'
        # ip3 = '192.168.0.123'
        # ixtla 2 
        ip1 = '192.168.0.120'
        lavadoras_map = {
            'Lavadora 1': (ip1, '1'),
            'Lavadora 2': (ip1, '2'),
            'Lavadora 3': (ip1, '3'),
            'Lavadora 4': (ip1, '4'),
            'Lavadora 5': (ip1, '5'),
            'Lavadora 6': (ip1, '6'),
            # 'Lavadora 7': (ip1, '7'),
            # 'Lavadora 8': (ip1, '8'),
            # 'Lavadora 9': (ip1, '9'),
            # 'Lavadora 10': (ip1, '10'),
            'Secadora 1': (ip1, '7'),
            'Secadora 2': (ip1, '8'),
            # 'Secadora 3': (ip1, '13'),
            # 'Secadora 4': (ip1, '14'),
            # 'Secadora 5': (ip1, '15'),
            # 'Secadora 6': (ip1, '16'),
        }

        if lavadora not in lavadoras_map:
            return JsonResponse({'message': 'Error: Lavadora o secadora no encontrada'}, status=400)

        ipServer, portRele = lavadoras_map[lavadora]

        try:
            # Construir la URL completa con el puerto
            url = f'http://{ipServer}:80/{portRele}'
            payload = {'activar': 1}
            response = requests.post(url, json=payload)
            # Lanza una excepción si la solicitud no fue exitosa
            response.raise_for_status()
            message = 'Activación guardada correctamente y solicitud enviada al ESP32.'

        except requests.RequestException as e:
            message = f'Error al enviar la solicitud al ESP32: {str(e)}'

        return JsonResponse({'message': message})

    else:
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)


from django.utils import timezone


def descontar_stock(productos_comprados):
    try:
        print(productos_comprados)

        # Usar una transacción para asegurar consistencia en la base de datos
        with transaction.atomic():
            for item in productos_comprados:
                nombre_producto = item.get('nombre', '').strip()
                cantidad_comprada = int(item.get('cantidad', 0))

                # Verificar si el producto es de tipo 'producto'
                producto = Producto.objects.filter(nombre=nombre_producto, tipo='producto').first()

                if not producto:
                    print(f"El producto '{nombre_producto}' no es de tipo 'producto' o no existe.")
                    continue  # Ignorar productos que no son de tipo 'producto'

                # Obtener el inventario asociado al producto
                try:
                    inventario = Inventario.objects.select_for_update().get(producto=producto)
                    print(inventario, "inventario")

                    # Verificar si hay suficiente stock
                    if inventario.cantidad < cantidad_comprada:
                        return False, f"No hay suficiente stock de {inventario.producto.nombre}. Stock actual: {inventario.cantidad}"

                    # Descontar la cantidad del inventario
                    inventario.cantidad -= cantidad_comprada
                    inventario.save()

                except Inventario.DoesNotExist:
                    return False, f"Inventario no encontrado para el producto {producto.nombre}."

        return True, "Stock descontado exitosamente."

    except Exception as e:
        return False, f"Error al descontar stock: {str(e)}"



def pagar_venta(request):
    # cajaAbierta = caja_open(request.user)
    # if not cajaAbierta:
    #     print(cajaAbierta)
    #     return JsonResponse({'error': 'No hay caja abierta'}, status=400)

    if request.method == 'POST':
        # Obtener el JSON enviado en el cuerpo de la solicitud
        data = json.loads(request.body)

        # Extraer los datos del JSON
        productos_comprados = data.get('productos', [])
        cliente = data.get('cliente', 'Publico General')

        importe_total = float(data.get('total'))
        metodo_pago = data.get('metodo_pago', "Efectivo")
        usuario = request.user

        if not productos_comprados:
            return JsonResponse({'error': 'No se han proporcionado productos para la venta.'}, status=400)

        # Descontar el stock utilizando la función
        resultado, mensaje = descontar_stock(productos_comprados)
        if not resultado:
            return JsonResponse({'error': mensaje}, status=400)

        # Si cliente tiene un valor válido, proceder con la creación de la venta
        if cliente:
            fecha_venta = timezone.now()
            # Crear la venta en la base de datos
            venta = Ventas.objects.create(cliente=cliente, productos=productos_comprados,importe_total=importe_total, fecha_venta=fecha_venta, metodo_pago=metodo_pago, )
            print(venta)
            #imprimir_ticket(venta)
            return JsonResponse({'message': 'Venta realizada correctamente'})
        else:
            # Si el cliente no está especificado, utilizar "Publico General" por defecto
            cliente = "Publico General"
            fecha_venta = timezone.now()

            # Crear la venta en la base de datos
            venta = Ventas.objects.create(cliente=cliente, productos=productos_comprados,importe_total=importe_total, fecha_venta=fecha_venta, usuario=usuario, metodo_pago=metodo_pago,)
            print(venta)
            # Imprimir el ticket
            #imprimir_ticket(venta)

            # Devolver una respuesta JSON indicando que la venta ha sido realizada correctamente
            # return JsonResponse({'message': 'Venta realizada correctamente con cliente por defecto (Publico General)'})
            return JsonResponse({'message': 'Venta realizada correctamente con cliente por defecto (Publico General)'})
    else:
        # Devolver una respuesta de error si no se recibe una solicitud POST
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)


def imprimir_ticket(venta):
    # Configura la impresora (ajusta los parámetros según tu impresora)
    p = Usb(0x0416, 0x5011, 0)  # Reemplaza con el Vendor ID y Product ID de tu impresora

    # Imprimir el logo (suponiendo que el logo está en el mismo directorio y se llama 'logo.png')
    p.set(align='center')
    p.image('img/icons8-lavadora-80.png')
    p.text("========== LAVANDEROS ==========\n")
    p.text("WhatsApp: 7222947337\n")
    p.text("Teléfono: 7229365461\n")
    p.text("Calle Paseo de los Matlatzincas 235\n")
    p.text("Col. Lomas Altas, Toluca, México\n")
    p.text("================================\n")
    p.text("Folio: {}\n".format(venta.id))
    p.text("================================\n")
    p.text("Cliente: {}\n".format(venta.cliente))
    p.text("================================\n")
    p.text("Atendió: {}\n".format(venta.usuario.username))
    p.text("================================\n")
    p.text("Fecha: {}\n".format(venta.fecha_venta.strftime("%d-%m-%Y %H:%M:%S")))
    p.text("================================\n")
    p.text("Cant    Descripción      Importe\n")
    p.text("--------------------------------\n")

    for producto in venta.productos:
        p.text("{: <8}{: <15} ${:.2f}\n".format(producto['cantidad'], producto['nombre'], producto['precio']))

    p.text("================================\n")
    p.text("Total: ${:.2f}\n".format(venta.importe_total))
    p.text("================================\n")
    p.text("\"Porque NO toda la ropa sucia se lava en casa\"\n")
    p.text("================================\n")

    p.cut()
    p.close()

# Imprimir ticket de encargo
def encargo_tiket(encargo):
    # Configura la impresora (ajusta los parámetros según tu impresora)
    p = Usb(0x0416, 0x5011, 0)  # Reemplaza con el Vendor ID y Product ID de tu impresora

    # Imprimir el logo (suponiendo que el logo está en el mismo directorio y se llama 'logo.png')
    p.set(align='center')
    p.image('img/icons8-lavadora-80.png')
    p.text("========== LAVANDEROS ==========\n")
    p.text("WhatsApp: 7222947337\n")
    p.text("Teléfono: 7229365461\n")
    p.text("Calle Paseo de los Matlatzincas 235\n")
    p.text("Col. Lomas Altas, Toluca, México\n")
    p.text("================================\n")
    p.text("Folio: {}\n".format(encargo.Folio))
    p.text("================================\n")
    p.text("Atendió: {}\n".format(encargo.usuario))
    p.text("================================\n")
    p.text("Fecha: {}\n".format(encargo.fecha_encargo.strftime("%d-%m-%Y %H:%M:%S")))
    p.text("================================\n")
    p.text("Cant    Descripción      Importe\n")
    p.text("--------------------------------\n")

    for encargo in encargo. venta.productos:
        p.text("{: <8}{: <15} ${:.2f}\n".format(producto['cantidad'], producto['nombre'], producto['precio']))


    p.text("================================\n")
    p.text("Total: ${:.2f}\n".format())
    p.text("================================\n")
    p.text("\"Porque NO toda la ropa sucia se lava en casa\"\n")
    p.text("================================\n")

    p.cut()
    p.close()


class CustomLoginView(LoginView):
    template_name = 'login.html'

@login_required
def logout_view(request):
    logout(request)
    # Redirigir a una página después del logout
    return redirect('login')

@superusuario_required
def crear_producto(request):
    productos = Producto.objects.all()

    if request.method == 'POST':
        # Obtener los datos del formulario enviado
        nombre = request.POST.get('nombre').strip()
        precio = request.POST.get('precio')
        codigo_barras = request.POST.get('codigo_barras')
        tipo = request.POST.get('tipo')

        if not codigo_barras:
            print("No se proporcionó un código de barras.")
            # Verificar si ya existe un producto con el mismo nombre
            if Producto.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, f"Ya existe un producto con el nombre '{nombre}'.")
                print("Ya existe un producto con el mismo nombre.")
                # return JsonResponse({'success': False, 'message': 'Ya existe un producto con el mismo nombre.'}, status=400)
            else:
                # Crear el producto si no hay duplicados
                producto = Producto(nombre=nombre, precio=precio, codigo_barras=codigo_barras, tipo=tipo)
                producto.save()
                messages.success(request, "Producto creado exitosamente.")
                print("Producto creado exitosamente.")
        
        else:
            print("Se proporcionó un código de barras.")
            # Verificar si ya existe un producto con el mismo nombre
            if Producto.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, f"Ya existe un producto con el nombre '{nombre}'.")
                print("Ya existe un producto con el mismo nombre.")
                # return JsonResponse({'success': False, 'message': 'Ya existe un producto con el mismo nombre.'}, status=400)
            elif Producto.objects.filter(codigo_barras__iexact=codigo_barras).exists():
                messages.error(request, f"Ya existe un producto con el código de barras '{codigo_barras}'.")
                print("Ya existe un producto con el mismo código de barras.")
                # return JsonResponse({'success': False, 'message': 'Ya existe un producto con el mismo código de barras.'}, status=400)
            else:
                # Crear el producto si no hay duplicados
                producto = Producto(nombre=nombre, precio=precio, codigo_barras=codigo_barras, tipo=tipo)
                producto.save()
                messages.success(request, "Producto creado exitosamente.")
                print("Producto creado exitosamente.")

        # Guardar los datos en el modelo Producto
        # producto = Producto(nombre=nombre, precio=precio, codigo_barras=codigo_barras, tipo=tipo)
        # producto.save()

        # Redirigir a la página de productos
        return redirect('crear_producto')

    else:
        return render(request, 'producto.html', {'productos': productos})

def eliminar_producto(request, producto_id):
    if request.method == 'DELETE':
        # Obtener el producto por su ID
        producto = Producto.objects.get(id=producto_id)
        # Eliminar el producto
        producto.delete()
        # Devolver una respuesta JSON indicando que la eliminación fue exitosa
        return JsonResponse({'message': 'Producto eliminado correctamente'})

    else:
        # Si la solicitud no es DELETE, devolver un error
        return JsonResponse({'error': 'Se esperaba una solicitud DELETE'}, status=400)


""" Acciones de la lista de precios """
@superusuario_required
def nuevo_precio(request):
    productos = Producto.objects.all()

    return render(request, 'encargo.html', {'precios': productos})



def eliminar_precio(request, precio_id):
    if request.method == 'DELETE':
        precio = get_object_or_404(lista_precios, id=precio_id)
        precio.delete()
        return JsonResponse({'message': 'Precio eliminado correctamente'})

    else:
        # Si la solicitud no es DELETE, devolver un error
        return JsonResponse({'error': 'Se esperaba una solicitud DELETE'}, status=400)


# @superusuario_required
# def corte_caja(request):
#     # Obtener la fecha actual
#     fecha_actual = timezone.now()

#     # Obtener la fecha del día anterior
#     fecha_anterior = fecha_actual - timezone.timedelta(days=1)


#     saldo_inicial = 0
#     saldo_inicial_query = TurnoCaja.objects.filter(fecha_cierre=fecha_actual)
#     if saldo_inicial_query.exists():
#         saldo_inicial = saldo_inicial_query.first().saldo_inicial
#         print(saldo_inicial)

#     # Filtrar los registros de ControlPagoEncargos para la fecha de encargo
#     pagos_recibidos = ControlPagoEncargos.objects.filter(fecha_encargo=fecha_actual).aggregate(total=Sum('pago_recibido'))['total'] or 0

#     # Filtrar los registros de ControlPagoEncargos para la fecha de entregado
#     adeudos = ControlPagoEncargos.objects.filter(fecha_entregado=fecha_actual).aggregate(total=Sum('adeudo'))['total'] or 0

#     total_encargos = pagos_recibidos + adeudos

#     # Filtrar los registros de Ventas para la fecha de venta
#     ventas_totales = Ventas.objects.filter(fecha_venta=fecha_actual).aggregate(total=Sum('importe_total'))['total'] or 0

#     # Calcular el saldo final total
#     saldo_final_total = pagos_recibidos + adeudos + ventas_totales + saldo_inicial

#     saldo_final_reportado_obj = SaldoFinalDiario.objects.filter(fecha=fecha_actual).first()
#     saldo_final_reportado = saldo_final_reportado_obj.saldo_final if saldo_final_reportado_obj else None
#     usuario_saldo_final = saldo_final_reportado_obj.usuario if saldo_final_reportado_obj else None


#     context = {
#         'fecha_actual': fecha_actual,
#         'total_ventas': ventas_totales,
#         'total_encargos': total_encargos,
#         'saldo_inicial': saldo_inicial,
#         'saldo_final': saldo_final_total,
#         'saldo_final_reportado': saldo_final_reportado,
#         'usuario_saldo_final': usuario_saldo_final,
#     }

#     # Renderizar la plantilla con los datos del corte de caja
#     return render(request, 'corte_caja.html', context)

@superusuario_required
def corte_caja(request):
    # Obtener la fecha seleccionada o usar la fecha actual
    fecha_seleccionada = request.GET.get('fecha')
    if fecha_seleccionada:
        # Convertir fecha seleccionada a aware datetime
        fecha_seleccionada = make_aware(datetime.strptime(fecha_seleccionada, '%Y-%m-%d'))
    else:
        fecha_seleccionada = timezone.now().date()

    # Filtrar turnos de caja con la fecha aware
    # turnos_caja = [turno for turno in TurnoCaja.objects.all() if turno.fecha_apertura.date() == fecha_seleccionada]
    turnos_caja = TurnoCaja.objects.filter(
        fecha_apertura__date=fecha_seleccionada,
        estado="cerrada"
    ).order_by("fecha_apertura")

    detalles_turnos = []
    # Variables para acumular totales
    ventas_totales = 0
    encargos_totales = 0

    for turno in turnos_caja:
        # Obtener la lista de ventas dentro del rango de apertura y cierre del turno
        ventas_turno = Ventas.objects.filter(
            fecha_venta__range=[turno.fecha_apertura, turno.fecha_cierre]
        )

        # Inicializar acumulador de importe total y lista de productos para el turno
        total_ventas_turno = 0
        productos_ventas_turno = []
        


        for venta in ventas_turno:
            productos = json.loads(venta.productos.replace("'", '"')) # Convertir string JSON a lista de productos
            productos_con_totales = [
                {
                    'nombre': producto['nombre'],
                    'precio': producto['precio'],
                    'cantidad': producto['cantidad'],
                    'total': float(producto['precio']) * producto['cantidad']
                }
                for producto in productos
            ]
            productos_ventas_turno.append({
                'cliente': venta.cliente,
                'metodo_pago': venta.metodo_pago,
                'productos': productos_con_totales,
                'importe_total': venta.importe_total,
            })
            total_ventas_turno += venta.importe_total


        pagos_recibidos_turno = ControlPagoEncargos.objects.filter(
            fecha_encargo__range=[turno.fecha_apertura, turno.fecha_cierre]
        ).aggregate(total=Sum('pago_recibido'))['total'] or 0

        pagos_recibidosEncargos = ControlPagoEncargos.objects.filter(
            fecha_encargo__range=[turno.fecha_apertura, turno.fecha_cierre],
            pago_recibido__gt=0
        )

        productos_encargos_turno = []
        for pago in pagos_recibidosEncargos:
            productos = json.loads(pago.productos.replace("'", '"'))  # Convertir a lista
            productos_con_totales = [
                {
                    'nombre': producto['nombre'],
                    'precio': producto['precio'],
                    'cantidad': producto['cantidad'],
                    'total': float(producto['precio']) * producto['cantidad']
                }
                for producto in productos
            ]
            productos_encargos_turno.append({
                'cliente': pago.encargo.cliente.nombre if pago.encargo.cliente else "Sin cliente",
                'metodo_pago': pago.encargo.forma_pago,
                'productos': productos_con_totales,
                'pago_recibido': pago.pago_recibido,
            })

        adeudos_turno = ControlPagoEncargos.objects.filter(
            fecha_entregado__range=[turno.fecha_apertura, turno.fecha_cierre],

        ).aggregate(total=Sum('adeudo'))['total'] or 0

        total_encargos = pagos_recibidos_turno + adeudos_turno
        # saldo_final = turno.saldo_inicial + ventas_turno + total_encargos
        saldo_final = turno.saldo_inicial + total_ventas_turno + total_encargos


        # Agregar los datos del turno al contexto
        detalles_turnos.append({
            'vendedor': turno.vendedor,
            'fecha_apertura': turno.fecha_apertura,
            'fecha_cierre': turno.fecha_cierre,
            'saldo_inicial': turno.saldo_inicial,
            'ventas': total_ventas_turno,
            'productos_ventas': productos_ventas_turno,
            'productos_encargos': productos_encargos_turno,
            'encargos': total_encargos,
            'saldo_final': saldo_final,
            'saldo_reportado': turno.saldo_final
        })

        ventas_totales += total_ventas_turno
        encargos_totales += total_encargos

    # Calcular totales
    saldo_inicial_total = sum(turno.saldo_inicial for turno in turnos_caja)
    saldo_final_total = sum(turno.saldo_final or 0 for turno in turnos_caja)

    # ventas_totales = Ventas.objects.filter(
    #     fecha_venta__date=fecha_seleccionada
    # ).aggregate(total=Sum('importe_total'))['total'] or 0

    # total_encargos = (
    #     ControlPagoEncargos.objects.filter(fecha_encargo__date=fecha_seleccionada).aggregate(total=Sum('pago_recibido'))['total'] or 0
    #     + ControlPagoEncargos.objects.filter(fecha_entregado__date=fecha_seleccionada).aggregate(total=Sum('adeudo'))['total'] or 0
    # )


    # Contexto para enviar a la plantilla
    context = {
        'fecha_actual': fecha_seleccionada,
        'turnos_caja': turnos_caja,
        'total_ventas': ventas_totales,
        'total_encargos': encargos_totales,
        'detalles_turnos': detalles_turnos,
        'saldo_inicial_total': saldo_inicial_total,
        'saldo_final_total': saldo_final_total,
    }

    return render(request, 'corte_caja.html', context)


def ingresar_saldo_final(request):

    if request.method == 'POST':
        saldo_final = request.POST.get('saldo_final')

        if saldo_final:
            usuario = request.user
            saldo_final = float(saldo_final)
            fecha = timezone.now()
            saldo_final_diario = SaldoFinalDiario(saldo_final=saldo_final, fecha=fecha)
            saldo_final_diario.save()
            logout(request)  # Cerrar sesión del usuario
            return redirect('login')  # Redirigir a la página de inicio de sesión

    return render(request, 'ingresar_saldo_final.html')


@login_required
def abrir_caja(request):
    caja_abierta = TurnoCaja.objects.filter(vendedor=request.user, estado="abierta").exists()

    if caja_abierta:
        return redirect('home')

    if request.method == 'POST':
        saldo_inicial = request.POST.get('saldo_inicial')
        if saldo_inicial:
            TurnoCaja.objects.create(
                vendedor=request.user,
                saldo_inicial=saldo_inicial,
                estado="abierta",
                fecha_apertura=timezone.now()
            )
            return JsonResponse({'success': True, 'message': 'Caja abierta con éxito', 'redirect_url': '/home'})

        else:
            return JsonResponse({'success': False, 'message': 'El saldo inicial es requerido'})

    return render(request, 'abrir_caja.html')

def caja_open(user):
    fecha_actual = timezone.now().date()
    if TurnoCaja.objects.filter(vendedor=user, fecha_apertura__date=fecha_actual, estado="abierta").exists():
        return True
    else:
        return False

@login_required
def cerrar_caja(request):
    if request.method == 'POST':
        saldo_final = request.POST.get('saldo_final')
        try:
            # Obtener el último turno de caja del usuario que aún está abierto (sin saldo final)
            turno = TurnoCaja.objects.filter(vendedor=request.user, estado="abierta").first()
            turno.saldo_final = saldo_final
            turno.fecha_cierre = timezone.now()
            turno.estado = "cerrada"
            turno.save()  # Calcular las ventas

            # Generar el ticket
            fecha_seleccionada = turno.fecha_apertura.date()  # La fecha del turno cerrado
            turnos_caja = TurnoCaja.objects.filter(
                fecha_apertura__date=fecha_seleccionada,
                estado="cerrada",
                vendedor=request.user
            ).order_by("fecha_apertura")

            detalles_turnos = []
            ventas_totales = 0
            encargos_totales = 0

            for turno in turnos_caja:
                # Ventas por turno
                ventas_turno = Ventas.objects.filter(
                    fecha_venta__range=[turno.fecha_apertura, turno.fecha_cierre]
                )

                total_ventas_turno = 0
                productos_ventas_turno = []

                for venta in ventas_turno:
                    productos = json.loads(venta.productos.replace("'", '"'))
                    productos_con_totales = [
                        {
                            'nombre': producto['nombre'],
                            'precio': producto['precio'],
                            'cantidad': producto['cantidad'],
                            'total': float(producto['precio']) * producto['cantidad']
                        }
                        for producto in productos
                    ]
                    productos_ventas_turno.append({
                        'cliente': venta.cliente,
                        'metodo_pago': venta.metodo_pago,
                        'productos': productos_con_totales,
                        'importe_total': venta.importe_total,
                    })
                    total_ventas_turno += venta.importe_total

                # Encargos
                pagos_recibidos_turno = ControlPagoEncargos.objects.filter(
                    fecha_encargo__range=[turno.fecha_apertura, turno.fecha_cierre]
                ).aggregate(total=Sum('pago_recibido'))['total'] or 0

                pagos_recibidosEncargos = ControlPagoEncargos.objects.filter(
                    fecha_encargo__range=[turno.fecha_apertura, turno.fecha_cierre],
                    pago_recibido__gt=0
                )

                productos_encargos_turno = []
                for pago in pagos_recibidosEncargos:
                    productos = json.loads(pago.productos.replace("'", '"'))  # Convertir a lista
                    productos_con_totales = [
                        {
                            'nombre': producto['nombre'],
                            'precio': producto['precio'],
                            'cantidad': producto['cantidad'],
                            'total': float(producto['precio']) * producto['cantidad']
                        }
                        for producto in productos
                    ]
                    productos_encargos_turno.append({
                        'cliente': pago.encargo.cliente.nombre if pago.encargo.cliente else "Sin cliente",
                        'metodo_pago': pago.encargo.forma_pago,
                        'productos': productos_con_totales,
                        'pago_recibido': pago.pago_recibido,
                    })

                adeudos_turno = ControlPagoEncargos.objects.filter(
                    fecha_entregado__range=[turno.fecha_apertura, turno.fecha_cierre]
                ).aggregate(total=Sum('adeudo'))['total'] or 0

                total_encargos = pagos_recibidos_turno + adeudos_turno
                saldo_final = turno.saldo_inicial + total_ventas_turno + total_encargos

                detalles_turnos.append({
                    'vendedor': turno.vendedor,
                    'fecha_apertura': turno.fecha_apertura,
                    'fecha_cierre': turno.fecha_cierre,
                    'saldo_inicial': turno.saldo_inicial,
                    'ventas': total_ventas_turno,
                    'productos_ventas': productos_ventas_turno,
                    'productos_encargos': productos_encargos_turno,
                    'encargos': total_encargos,
                    'saldo_final': saldo_final,
                    'saldo_reportado': turno.saldo_final
                })

                ventas_totales += total_ventas_turno
                encargos_totales += total_encargos

            # Generar el ticket HTML
            ticket_html = generar_ticket(detalles_turnos, timezone.now().strftime("%Y-%m-%d"))


            # logout(request)
            return JsonResponse({'success': True, 'message': 'Caja cerrada con éxito','ticket': ticket_html, 'redirect_url': '/logout'})

        except TurnoCaja.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No hay un turno de caja abierto'})

    return render(request, 'cerrar_caja.html')



def generar_ticket(detalles_turnos, fecha):
    ticket_html = f"""
    <div style="font-family: 'Ticketing', sans-serif; font-size: 1.5em;">
        <!-- Encabezado -->
        <h2 style="text-align: center; margin: 5px 0;">Lavanderos</h2>
        <p style="text-align: center; margin: 5px 0;">WhatsApp: 7222947337</p>
        <p style="text-align: center; margin: 5px 0;">Teléfono: 7229365461</p>
        <p style="text-align: center; margin: 5px 0;">Av. Gustavo Baz Esq. con Av. de la Mujer</p>
        <p style="text-align: center; margin: 5px 0;">SN, Ixtlahuaca de Rayón, Edomex, México</p>
        <hr style="border: 1px dashed #000;">

        <!-- Fecha -->
        <p style="text-align: center;">Fecha: {fecha}</p>
        <hr style="border: 1px dashed #000;">

        <!-- Detalles de turnos -->
    """
    for turno in detalles_turnos:
        ticket_html += f"""
        <div>
            <h4 style="text-align: center; margin: 5px 0;">Turno de {turno['vendedor']}</h4>
            <p>Apertura: {turno['fecha_apertura'].strftime("%H:%M")} | Cierre: {turno['fecha_cierre'].strftime("%H:%M")}</p>
            <p>Saldo Inicial: ${turno['saldo_inicial']:.2f}</p>
            <p>Ventas: ${turno['ventas']:.2f}</p>
            <p>Encargos: ${turno['encargos']:.2f}</p>
            <p>Saldo Final: ${turno['saldo_final']:.2f}</p>
            <p>Saldo Reportado: ${turno['saldo_reportado']:.2f}</p>

            <!-- Productos vendidos -->
            <h5 style="text-align: center; margin: 10px 0;">Productos Vendidos</h5>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9em;">
                <thead>
                    <tr>
                        <th style="border-bottom: 1px solid #000; text-align: left;">Producto</th>
                        <th style="border-bottom: 1px solid #000; text-align: center;">Cant.</th>
                        <th style="border-bottom: 1px solid #000; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
        """
        for venta in turno['productos_ventas']:
            for producto in venta['productos']:
                ticket_html += f"""
                <tr>
                    <td>{producto['nombre']}</td>
                    <td style="text-align: center;">{producto['cantidad']}</td>
                    <td style="text-align: right;">${producto['total']:.2f}</td>
                </tr>
                """
        for encargo in turno['productos_encargos']:
            for producto in encargo['productos']:
                ticket_html += f"""
                <tr>
                    <td>{producto['nombre']}</td>
                    <td style="text-align: center;">{producto['cantidad']}</td>
                    <td style="text-align: right;">${producto['total']:.2f}</td>
                </tr>
                """

        ticket_html += """
                </tbody>
            </table>
            <hr style="border: 1px dashed #000;">
        </div>
        """

    ticket_html += "</div>"  # Cerrar contenedor principal
    return ticket_html


@receiver(post_save, sender=Producto)
def crear_inventario(sender, instance, created, **kwargs):
    if created and instance.tipo == "producto":
        Inventario.objects.create(producto=instance)


@superusuario_required
def inventario_view(request):
    productos = Producto.objects.filter(tipo="producto").select_related('inventario').order_by('nombre')

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad_a_agregar = int(request.POST.get('cantidad', 0))

        inventario = get_object_or_404(Inventario, producto_id=producto_id)
        inventario.cantidad += cantidad_a_agregar
        inventario.save()

        return JsonResponse({'success': True, 'message': 'Cantidad actualizada con éxito'})

    return render(request, 'inventario.html', {'productos': productos})
