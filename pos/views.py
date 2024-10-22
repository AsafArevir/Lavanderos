# Librerias e importacion de elementos en django
from django.shortcuts import render
from .models import Producto, Cliente, Encargo, Activacion, Ventas, ControlPagoEncargos, SaldoFinalDiario, lista_precios, PagosEncargos
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
from django.utils import timezone

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
    encargos_proceso = Encargo.objects.filter(estado='EN_PROCESO')
    encargos_completado = Encargo.objects.filter(estado='COMPLETADO')
    encargos_entregados = Encargo.objects.filter(estado='ENTREGADO')
    clientes = Cliente.objects.all()
    
    context = {
        'encargos_encargo': encargos_encargo,
        'encargos_proceso': encargos_proceso,
        'encargos_completado': encargos_completado,
        'encargos_entregados': encargos_entregados,
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
            encargo2 = PagosEncargos(encargoCompleto=encargo, fecha=timezone.now().date(), pago=adeudo_original)
            encargo2.save()
            encargo.save()

            control_pago_encargo = get_object_or_404(ControlPagoEncargos, encargo=encargo)
            if nuevo_adeudo == 0:
                control_pago_encargo.fecha_entregado = timezone.now().date()

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

            encargo = Encargo(
                Folio=folio,
                fecha_encargo=fecha_encargo,
                fecha_entrega=fecha_entrega,
                cliente_id=cliente_id,
                estado='EN_PROCESO',
                costo=costo,
                adeudo=adeudo,
                ingreso=ingreso,
                usuario=request.user,
                observaciones=observaciones,
                forma_pago=forma_pago
            )
            encargo.save()

            # Registro para el control de pagos
            ControlPagoEncargos.objects.create(
                encargo=encargo,
                fecha_encargo=fecha_encargo,
                pago_recibido=ingreso,
                adeudo=adeudo,
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

        #IP server EPSP32
        # 
        ipServer='192.168.101.120'       

        # Enviar la solicitud HTTP al ESP32
        if lavadora == 'Lavadora 1':
            portRele = '1'
        elif lavadora == 'Lavadora 2':
            portRele = '2'
        elif lavadora == 'Lavadora 3':
            portRele = '3' 
        elif lavadora == 'Lavadora 4':
            portRele = '4'
        elif lavadora == 'Lavadora 5':
            portRele = '6'
        elif lavadora == 'Lavadora 6':
            portRele = '7'
        elif lavadora == 'Lavadora 8':
            portRele = '8'
        elif lavadora == 'Lavadora 9':
            portRele = '9'
        elif lavadora == 'Lavadora 10':
            portRele = '10'
        
        """Añadir más condiciones para las otras lavadoras si es necesario"""

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

def pagar_venta(request):
    if request.method == 'POST':
        # Obtener el JSON enviado en el cuerpo de la solicitud
        data = json.loads(request.body)
        
        # Extraer los datos del JSON
        productos_comprados = data.get('productos', [])
        cliente = data.get('cliente', 'Publico General')
        
        importe_total = float(data.get('total'))
        metodo_pago = data.get('metodo_pago', "Efectivo")
        usuario = request.user

        # Si cliente tiene un valor válido, proceder con la creación de la venta
        if cliente:
            fecha_venta = timezone.now()
            # Crear la venta en la base de datos
            venta = Ventas.objects.create(cliente=cliente, productos=productos_comprados,importe_total=importe_total, fecha_venta=fecha_venta, metodo_pago=metodo_pago, )
            
            #imprimir_ticket(venta)
            return JsonResponse({'message': 'Venta realizada correctamente'})
        else:
            # Si el cliente no está especificado, utilizar "Publico General" por defecto
            cliente = "Publico General"
            fecha_venta = timezone.now()

            # Crear la venta en la base de datos
            venta = Ventas.objects.create(cliente=cliente, productos=productos_comprados,importe_total=importe_total, fecha_venta=fecha_venta, usuario=usuario, metodo_pago=metodo_pago,)
            
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
        nombre = request.POST.get('nombre')
        precio = request.POST.get('precio')
        codigo_barras = request.POST.get('codigo_barras')
        tipo = request.POST.get('tipo')

        # Guardar los datos en el modelo Producto
        producto = Producto(nombre=nombre, precio=precio, codigo_barras=codigo_barras, tipo=tipo)
        producto.save()

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
    precios = lista_precios.objects.all()

    if request.method == 'POST':
        # Obtener los datos del formulario enviado
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')

        # Guardar los datos en el modelo
        new_price = lista_precios(Nombre=nombre, Descripcion=descripcion, Precio=precio)
        new_price.save()

        # Redirigir a la página de productos
        return redirect('nuevo_precio')
    
    return render(request, 'encargo.html', {'precios': precios})


def eliminar_precio(request, precio_id):
    if request.method == 'DELETE':
        precio = get_object_or_404(lista_precios, id=precio_id)
        precio.delete()
        return JsonResponse({'message': 'Precio eliminado correctamente'})
    
    else:
        # Si la solicitud no es DELETE, devolver un error
        return JsonResponse({'error': 'Se esperaba una solicitud DELETE'}, status=400)
    

@superusuario_required
def corte_caja(request):    
    # Obtener la fecha actual
    fecha_actual = timezone.now().date()
    
    # Obtener la fecha del día anterior
    fecha_anterior = fecha_actual - timezone.timedelta(days=1)

    # Obtener el saldo inicial del día anterior, si existe
    saldo_inicial = 0
    saldo_inicial_query = SaldoFinalDiario.objects.filter(fecha=fecha_anterior)
    if saldo_inicial_query.exists():
        saldo_inicial = saldo_inicial_query.first().saldo_final

    # Filtrar los registros de ControlPagoEncargos para la fecha de encargo
    pagos_recibidos = ControlPagoEncargos.objects.filter(fecha_encargo=fecha_actual).aggregate(total=Sum('pago_recibido'))['total'] or 0
    
    # Filtrar los registros de ControlPagoEncargos para la fecha de entregado
    adeudos = ControlPagoEncargos.objects.filter(fecha_entregado=fecha_actual).aggregate(total=Sum('adeudo'))['total'] or 0
    
    total_encargos = pagos_recibidos + adeudos
    
    # Filtrar los registros de Ventas para la fecha de venta
    ventas_totales = Ventas.objects.filter(fecha_venta=fecha_actual).aggregate(total=Sum('importe_total'))['total'] or 0
    
    # Calcular el saldo final total
    saldo_final_total = pagos_recibidos + adeudos + ventas_totales + saldo_inicial
    
    saldo_final_reportado_obj = SaldoFinalDiario.objects.filter(fecha=fecha_actual).first()
    saldo_final_reportado = saldo_final_reportado_obj.saldo_final if saldo_final_reportado_obj else None
    usuario_saldo_final = saldo_final_reportado_obj.usuario if saldo_final_reportado_obj else None
        
        
    context = {
        'fecha_actual': fecha_actual,
        'total_ventas': ventas_totales,
        'total_encargos': total_encargos,
        'saldo_inicial': saldo_inicial,
        'saldo_final': saldo_final_total,
        'saldo_final_reportado': saldo_final_reportado,
        'usuario_saldo_final': usuario_saldo_final,
    }

    # Renderizar la plantilla con los datos del corte de caja
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


