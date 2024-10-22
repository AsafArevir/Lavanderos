document.addEventListener('DOMContentLoaded', function() {
    var btnCambiarEstado = document.querySelectorAll('.btn-cambiar-estado');

    btnCambiarEstado.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var encargoId = this.dataset.id;
            var modal = $('#modalCambiarEstado');
            modal.modal('show');

            // Obtener el adeudo actual
            $.ajax({
                type: 'GET',
                url: '/cambiar-estado-encargo/' + encargoId + '/',
                success: function(response) {
                    var adeudo = response.adeudo;
                    $('#selectAdeudo').val(adeudo);

                    // Ajustar el campo "Nuevo Adeudo" según la selección del usuario
                    $('#selectPago').off('change').on('change', function() {
                        if ($(this).val() == '1') { // Pagado
                            $('#selectAdeudo').val('0.00').prop('readonly', true);
                        } else { // Adeuda
                            $('#selectAdeudo').val(adeudo).prop('readonly', true);
                        }
                    });

                    // Inicializa el valor del campo "Nuevo Adeudo" según el estado actual
                    $('#selectPago').trigger('change');
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });

            // Enviar solicitud al servidor para cambiar el estado
            $('#formCambiarEstado').off('submit').on('submit', function(e) {
                e.preventDefault();
                var nuevoEstado = $('#selectEstado').val();
                var nuevoPago = $('#selectPago').val();
                var nuevoAdeudo = $('#selectAdeudo').val();
                var estadoEntrega = $('#estadoEntrega').val();

                $.ajax({
                    type: 'POST',
                    url: '/cambiar-estado-encargo/' + encargoId + '/',
                    data: {
                        nuevo_estado: nuevoEstado,
                        nuevo_pago: nuevoPago,
                        nuevo_adeudo: nuevoAdeudo,
                        estado_entrega: estadoEntrega,
                        csrfmiddlewaretoken: '{{ csrf_token }}'
                    },
                    success: function(response) {
                        modal.modal('hide');
                        showToast('Encargo actualizado', 'success');
                        setTimeout(function() {
                            location.reload();
                        }, 3000);
                    },
                    error: function(xhr, errmsg, err) {
                        console.log(xhr.status + ": " + xhr.responseText);
                        showToast('Error al actualizar el encargo', 'error');
                    }
                });
            });
        });
    });
});

// Función para mostrar un toast
function showToast(message, type) {
    var toast = new bootstrap.Toast(document.getElementById('toastNotification'));
    document.getElementById('toastBody').innerText = message;
    document.getElementById('toastNotification').classList.add('bg-' + type);
    toast.show();
}
        
// Control de acciones en el formulario
document.addEventListener('DOMContentLoaded', function() {
    var modal = new bootstrap.Modal(document.getElementById('modalAgregarEncargo'));

    document.getElementById('formAgregarEncargo').addEventListener('submit', function(event) {
        event.preventDefault();

        var formData = new FormData(this);
        var activeTab = document.querySelector('.nav-link.active').id;
        var url = '/guardar-encargo/';

        switch (activeTab) {
            case 'encargo-tab':
                url = '/guardar-encargo/';
                break;
            case 'proceso-tab':
                url = '/guardar-encargo-proceso/';
                break;
            case 'completado-tab':
                url = '/guardar-encargo-completado/';
                break;
            default:
                break;
        }

        // Envio de la informacion al servidor por medio de AJAX
        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error al guardar el encargo');
        })
        .then(data => {
            console.log('Encargo guardado:', data);
            modal.hide(); // Ocultar el modal después de guardar
            resetForm(); // Llamar a la función para limpiar el formulario
            // Recargar la página después de 2 segundos (ajustable según sea necesario)
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    // Función para limpiar el formulario
    function resetForm() {
        document.getElementById('formAgregarEncargo').reset(); // Resetear el formulario

        // Asignacion de la fecha del dia que se ejecuta la alta del encargo
        document.getElementById('fecha_encargo').valueAsDate = new Date();

        // Limpiar campos adicionales si es necesario
        document.getElementById('anticipo').value = '';
        document.getElementById('adeudo').value = '';
        document.getElementById('pagadoCheckbox').checked = false;
        document.getElementById('anticipo').disabled = false;
    }

    // Asignacion de la fecha del dia que se ejecuta la alta del encargo
    document.getElementById('fecha_encargo').valueAsDate = new Date();

    // Calculo del adeudo enbase al costo y el anticipo
    var costoField = document.getElementById('costo');
    var anticipoField = document.getElementById('anticipo');
    var adeudoField = document.getElementById('adeudo');
    var pagadoIcon = document.getElementById('pagadoIcon');

    function calculateAdeudo() {
        var costo = parseFloat(costoField.value) || 0;
        var anticipo = parseFloat(anticipoField.value) || 0;
        var adeudo = costo - anticipo;
        adeudoField.value = adeudo.toFixed(2);
    }

    costoField.addEventListener('input', calculateAdeudo);
    anticipoField.addEventListener('input', calculateAdeudo);

    // Validacion de todo pagado mediante el checkbox
    var pagadoCheckbox = document.getElementById('pagadoCheckbox');

    pagadoCheckbox.addEventListener('change', function() {
        if (pagadoCheckbox.checked) {
            anticipoField.value = costoField.value;
            anticipoField.disabled = true;
            calculateAdeudo();
            pagadoIcon.style.display = 'inline'; // Mostrar el símbolo "✔"
        } else {
            anticipoField.disabled = false;
            calculateAdeudo();
            pagadoIcon.style.display = 'none'; // Ocultar el símbolo "✔"
        }
    });

    
});


        