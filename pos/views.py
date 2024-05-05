from django.shortcuts import render
from .models import Producto, Cliente, Encargo, Activacion, Ventas, ControlPagoEncargos, SaldoFinalDiario
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import requests, json
from django.contrib.auth.views import LoginView
from .decorators import superusuario_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db.models import Sum

@login_required
def inicio(request):
    return render(request, 'inicio.html')


@login_required
def productos(request):
    productos = Producto.objects.all()
    clientes = Cliente.objects.all()
    return render(request, 'productos.html', {'productos': productos, 'clientes': clientes})


@login_required
def clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes.html', {'clientes': clientes})


def agregar_cliente(request):
    if request.method == 'POST':
        # Obtener los datos del formulario enviado
        nombre = request.POST.get('nombre')
        apellidos = request.POST.get('apellidos')
        telefono = request.POST.get('telefono')
        correo = request.POST.get('correo')

        # Guardar los datos en el modelo Cliente
        cliente = Cliente(nombre=nombre, apellidos=apellidos, telefono=telefono, correo=correo)
        cliente.save()

        # Devolver una respuesta JSON con un mensaje de éxito
        return JsonResponse({'mensaje': 'Cliente agregado correctamente'}, status=201)
    else:
        # Si la solicitud no es POST, devolver un mensaje de error
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)

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


@login_required
def encargo(request):
    # Obtener encargos según su estado
    encargos_encargo = Encargo.objects.filter(estado='ENCARGO')
    encargos_proceso = Encargo.objects.filter(estado='EN_PROCESO')
    encargos_completado = Encargo.objects.filter(estado='COMPLETADO')
    encargos_entregados = Encargo.objects.filter(estado='ENTREGADO')
    # Obtener la lista de clientes
    clientes = Cliente.objects.all()
    
    # Enviar los encargos como contexto a la plantilla
    context = {
        'encargos_encargo': encargos_encargo,
        'encargos_proceso': encargos_proceso,
        'encargos_completado': encargos_completado,
        'encargos_entregados': encargos_entregados,
        'clientes': clientes,
    }
    return render(request, 'encargos.html', context)


@require_POST
def cambiar_estado_encargo(request, encargo_id):
    nuevo_estado = request.POST.get('nuevo_estado')
    nuevo_pago = request.POST.get('nuevo_pago')
    nuevo_adeudo = request.POST.get('nuevo_adeudo')

    try:
        encargo = Encargo.objects.get(pk=encargo_id)
        encargo.estado = nuevo_estado
        encargo.pagado = bool(int(nuevo_pago))
        encargo.adeudo = float(nuevo_adeudo)
        encargo.save()
        
        if nuevo_estado == 'ENTREGADO':
            control_pago_encargo = ControlPagoEncargos.objects.get(encargo=encargo)
            control_pago_encargo.fecha_entregado = timezone.now()
            control_pago_encargo.save()
            
        return JsonResponse({'message': 'Encargo actualizado correctamente'}, status=200)
    except Encargo.DoesNotExist:
        return JsonResponse({'error': 'El encargo no existe'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def guardar_encargo(request):
    if request.method == 'POST':
        # Obtener los datos del formulario de la solicitud POST
        cliente_id = request.POST.get('cliente_id')
        fecha_encargo = request.POST.get('fecha_encargo')
        fecha_entrega = request.POST.get('fecha_entrega')
        costo = request.POST.get('costo')
        estado = 'ENCARGO'
        adeudo = request.POST.get('adeudo')
        
        pagado_str = request.POST.get('pagado')
        usuario = request.user
        # Convertir el valor de "pagado" a un booleano si es válido
        if pagado_str is not None:
            pagado = bool(int(pagado_str))
        else:
            pagado = False

        # Crear una instancia de Encargo y guardarla en la base de datos
        encargo = Encargo(
            cliente_id=cliente_id,
            fecha_encargo=fecha_encargo,
            fecha_entrega=fecha_entrega,
            costo=costo,
            estado=estado,
            pagado=pagado,
            adeudo=adeudo,
            usuario=usuario
        )
        encargo.save()
        
        pago_rec= float(costo) - float(adeudo)
        
        control_pago_encargo = ControlPagoEncargos(
            encargo=encargo,
            fecha_encargo=fecha_encargo,
            pago_recibido=pago_rec,
            adeudo=adeudo
        )
        control_pago_encargo.save()

        # Devolver una respuesta JSON indicando que el encargo ha sido guardado
        return JsonResponse({'message': 'Encargo guardado correctamente'})
    else:
        # Devolver una respuesta de error si no se recibe una solicitud POST
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)


@login_required
def lavadoras(request):
    activaciones = Activacion.objects.order_by('-fecha')
    return render(request, 'lavadoras.html', {'activaciones': activaciones})

def guardar_activacion(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        lavadora = request.POST.get('lavadora')
        motivo = request.POST.get('motivo')
        comentario = request.POST.get('comentario')
        usuario = request.user.username
        
        # Guardar los datos en la base de datos
        activacion = Activacion(
            lavadora=lavadora,
            motivo=motivo,
            comentario=comentario,
            fecha = timezone.now(),
            usuario=usuario
        )
        activacion.save()

        # Enviar la solicitud HTTP al ESP32
        if lavadora == 'Lavadora 1':
            ip = '192.168.0.201'
        elif lavadora == 'Lavadora 2':
            ip = '192.168.0.202'
        
        elif lavadora == 'Lavadora 3':
            ip = '192.168.0.203'
            
        elif lavadora == 'Lavadora 4':
            ip = '192.168.0.204'
            
        elif lavadora == 'Lavadora 5':
            ip = '192.168.0.205'
            
        elif lavadora == 'Lavadora 6':
            ip = '192.168.1.206'
            
        elif lavadora == 'Lavadora 7':
            ip = '192.168.0.207'
        # Añadir más condiciones para las otras lavadoras si es necesario

        try:
            url = f'http://{ip}:80'  # Construir la URL completa con el puerto
            payload = {'activar': 1}
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa
            message = 'Activación guardada correctamente y solicitud enviada al ESP32.'
        except requests.RequestException as e:
            message = f'Error al enviar la solicitud al ESP32: {str(e)}'

        # Devolver una respuesta JSON indicando que la activación ha sido guardada
        return JsonResponse({'message': message})
    else:
        # Devolver una respuesta de error si no se recibe una solicitud POST
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
        usuario = request.user

        # Si cliente tiene un valor válido, proceder con la creación de la venta
        if cliente:
            fecha_venta = timezone.now()

            # Crear la venta en la base de datos
            venta = Ventas.objects.create(cliente=cliente, productos=productos_comprados,importe_total=importe_total, fecha_venta=fecha_venta)
            # Devolver una respuesta JSON indicando que la venta ha sido realizada correctamente
            return JsonResponse({'message': 'Venta realizada correctamente'})
        else:
            # Si el cliente no está especificado, utilizar "Publico General" por defecto
            cliente = "Publico General"
            fecha_venta = timezone.now()

            # Crear la venta en la base de datos
            venta = Ventas.objects.create(cliente=cliente, productos=productos_comprados,importe_total=importe_total, fecha_venta=fecha_venta, usuario=usuario)
            
            # Devolver una respuesta JSON indicando que la venta ha sido realizada correctamente
            return JsonResponse({'message': 'Venta realizada correctamente con cliente por defecto (Publico General)'})
    else:
        # Devolver una respuesta de error si no se recibe una solicitud POST
        return JsonResponse({'error': 'Se esperaba una solicitud POST'}, status=400)

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

        # Guardar los datos en el modelo Producto
        producto = Producto(nombre=nombre, precio=precio)
        producto.save()

        # Redirigir a la página de productos
        return redirect('productos')
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
    
    saldo_final_reportado = SaldoFinalDiario.objects.filter(fecha=fecha_actual).first().saldo_final
    # Pasar los datos a la plantilla
    
    usuario_saldo_final = None
    saldo_final_query = SaldoFinalDiario.objects.filter(fecha=fecha_actual)
    if saldo_final_query.exists():
        usuario_saldo_final = saldo_final_query.first().usuario
        
        
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