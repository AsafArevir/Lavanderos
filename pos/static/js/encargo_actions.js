// Operaciones de la seccion encargos
document.addEventListener('DOMContentLoaded', function() {

    //Variables de los datos a agregar en el control de encargos.
    const formAgregarEncargo = document.getElementById('formAgregarEncargo');
    const folioInput = document.getElementById('folio');
    const fechaEncargoInput = document.getElementById('fecha_encargo');
    const anticipoInput = document.getElementById('anticipo');
    const costoInput = document.getElementById('costo');
    const adeudoInput = document.getElementById('adeudo');
    const pagadoCheckbox = document.getElementById('pagadoCheckbox');
    const forma_pago = document.getElementById('forma_pago');
    const observacionesInput = document.getElementById('observaciones');

    function generarFolio() {
        const now = new Date();
        const folio = now.getFullYear().toString() + 
                      (now.getMonth() + 1).toString().padStart(2, '0') + 
                      now.getDate().toString().padStart(2, '0') + 
                      now.getHours().toString().padStart(2, '0') + 
                      now.getMinutes().toString().padStart(2, '0') + 
                      now.getSeconds().toString().padStart(2, '0');
        folioInput.value = folio;
    }

    function actualizarAdeudo() {
        const costo = parseFloat(costoInput.value) || 0;
        const anticipo = parseFloat(anticipoInput.value) || 0;
        adeudoInput.value = (costo - anticipo).toFixed(2);
    }

    function manejarCheckboxPagado() {
        if (pagadoCheckbox.checked) {
            anticipoInput.value = costoInput.value;
            anticipoInput.readOnly = true;
            actualizarAdeudo();
        } else {
            anticipoInput.readOnly = false;
            actualizarAdeudo();
        }
    }

    $('#modalAgregarEncargo').on('show.bs.modal', function() {
        generarFolio();
        fechaEncargoInput.valueAsDate = new Date();
        manejarCheckboxPagado();
        
    });

    anticipoInput.addEventListener('input', actualizarAdeudo);
    costoInput.addEventListener('input', actualizarAdeudo);
    pagadoCheckbox.addEventListener('change', manejarCheckboxPagado);

    formAgregarEncargo.addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(formAgregarEncargo);
        fetch('/guardar-encargo/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(folioInput.value)
            const toastBody = document.getElementById('toastBody');
            toastBody.textContent = data.message;
            const toast = new bootstrap.Toast(document.getElementById('toastNotification'));
            toast.show();

            //Seccion para generar el conteido del ticket 
            generarTicket(folioInput.value, fechaEncargoInput.valueAsDate, forma_pago.value, costoInput.value, anticipoInput.value, observacionesInput.value);
            var modalTicket = new bootstrap.Modal(document.getElementById('modalTicket'));
            modalTicket.show();

            formAgregarEncargo.reset();
            $('#modalAgregarEncargo').modal('hide');
            //setTimeout(() => location.reload(), 2000);
        })
        .catch(error => console.error('Error:', error));
    });

    // Función para generar el contenido del ticket
    function generarTicket(folioInput, fechaEncargoInput, forma_pago, costoInput, anticipoInput, observacionesInput) {
        var ticketContent = document.getElementById('ticketContent');
        ticketContent.innerHTML = `
            <div style="text-align: right;">
            <img src={% static 'img/LAVANDEROS.ico' %} alt="Lavanderos" style="width: 100px; height: auto;"/>
            </div>
            <h2 style="text-align: center;">Lavanderos</h2>
            <p>WhatsApp: 7222947337</p>
            <p>Teléfono: 7229365461</p>
            <p>Calle Paseo de los Matlatzincas 235</p>
            <p>Col. Lomas Altas, Toluca, México</p>
            <h4>Informacion del encargo:</h4>
            <p>Fecha de emision: ${fechaEncargoInput}</p>
            <p>Folio: ${folioInput} </p>
            <p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>
            <p>Método de Pago: ${forma_pago}</p>
            <p>Descripcion: ${observacionesInput} </p>
            <p>Cantidad cubierta: ${anticipoInput}</p>
            <p class="total" style="text-align: right;">Total: $${parseFloat(costoInput).toFixed(2)}</p>
            <p>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~</p>
            <p style="font-style: italic; text-align: center;">"Porque NO toda la ropa sucia se lava en casa"</p>
            <p style="font-size: 0.8em; text-align: justify;"><i>"Lavanderos"</i>,después de <b> 2 meses</b> la empresa no se hace responsable de las prendas. Por su comprensión, gracias.</p>
        `;
    }

    $('.btn-imprime-ticket').on('click', function printTickett() {
        var printContents = document.getElementById('ticketContent').innerHTML;
        var originalContents = document.body.innerHTML;

        document.body.innerHTML = printContents;
        window.print();
        document.body.innerHTML = originalContents;

        // Reload the page after printing
        setTimeout(function() {
            location.reload();
        }, 1000);
    })

    // Validación de los datos de encargo
    $('.btn-cambiar-encargo').on('click', function() {
        const encargoId = $(this).data('id');
        const modal = $('#CambiarEstado');
        modal.modal('show');

        $.ajax({
            type: 'GET',
            url: '/cambiar-estado-encargo/' + encargoId + '/',
            success: function(response) {
                const adeudo = response.adeudo;
                const estado = response.estado;
                $('#estadoPago').val(adeudo);

                if (adeudo > 0) {
                    $('#nuevoAdeudoContainer').show();
                } else {
                    $('#nuevoAdeudoContainer').hide();
                }

            
                if (estado === 'ENTREGADO') {
                    $('#choseeContainer').show(); 
                    $('#nuevoAdeudoContainer').show(); 
                    $('#estadoPagoContainer').show(); 
                } else {
                    $('#choseeContainer').show();
                    $('#nuevoAdeudoContainer').hide(); 
                    $('#estadoPagoContainer').hide(); 
                }
            },
            error: function(xhr, errmsg, err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });

        $('#CambiarEstado').off('submit').on('submit', function(e) {
            e.preventDefault();
        
            const nuevoAdeudo = parseFloat($('#nuevoAdeudo').val()) || 0;
            const estadoPago = parseFloat($('#estadoPago').val());
            const estadoSeleccionado = $('#selectEstadot').val(); 
            const entregado = estadoSeleccionado === 'ENTREGADO'; 
        
            // Solo calculamos nuevo adeudo si estamos en estado 'ENTREGADO'
            const adeudoFinal = estadoSeleccionado === 'ENTREGADO' ? estadoPago - nuevoAdeudo : estadoPago;
        
            $.ajax({
                type: 'POST',
                url: '/cambiar-estado-encargo/' + encargoId + '/',
                data: {
                    estado: estadoSeleccionado,
                    ingreso: nuevoAdeudo,
                    nuevo_adeudo: adeudoFinal,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                },
                success: function(response) {
                    modal.modal('hide');
                    showToast('Encargo actualizado', 'success');
                    setTimeout(() => location.reload(), 3000);
                },
                error: function(xhr, errmsg, err) {
                    console.log(xhr.status + ": " + xhr.responseText);
                    showToast('Error al actualizar el encargo', 'error');
                }
            });
        });
        
    });

    function showToast(message, type) {
        const toastBody = document.getElementById('toastBody');
        toastBody.innerText = message;
        const toast = new bootstrap.Toast(document.getElementById('toastNotification'));
        toast.show();
    }
});
     
        