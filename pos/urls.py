from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('home/', views.inicio, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('productos/', views.productos, name='productos'),
    path('clientes/', views.clientes, name='clientes'),
    path('agregar-cliente/', views.agregar_cliente, name='agregar_cliente'),
    path('eliminar-cliente/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('encargos/', views.encargo, name='encargos'),
    path('cambiar-estado-encargo/<int:encargo_id>/', views.cambiar_estado_encargo, name='cambiar_estado_encargo'),
    path('guardar-encargo/', views.guardar_encargo, name='guardar_encargo'),
    path('lavadoras/', views.lavadoras, name='lavadoras'),
    path('guardar-activacion/', views.guardar_activacion, name='guardar_activacion'),
    path('pagar_venta/', views.pagar_venta, name='pagar_venta'),
    path('logout/', views.logout_view, name='logout'),
    path('crear_producto/', views.crear_producto, name='crear_producto'),
    path('eliminar_producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('corte_caja/', views.corte_caja, name='corte_caja'),
    path('ingresar_saldo_final/', views.ingresar_saldo_final, name='ingresar_saldo_final'),
]
