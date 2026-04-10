$(document).ready(function() {

    // --- 1. FUNCIONES DE INTERFAZ ---

    $(document).on('click', '.toggle-password', function() {
        const input = $(this).siblings('input');
        
        if (input.attr('type') === "password") {
            input.attr('type', 'text');
            $(this).removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            $(this).removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });

    window.abrirModal = function() {
        $('#modalLegal').css('display', 'flex');
    };

    window.cerrarModal = function() {
        $('#modalLegal').hide();
    };

    window.validarBoton = function() {
        const estaChequeado = $('#acepto-datos').is(':checked');
        $('#btn-envio').prop('disabled', !estaChequeado);
    };


    // --- 2. LÓGICA DE REGISTRO (PASO 1) ---

    window.simularEnvio = function() {
        const nom   = $('#nom').val().trim();
        const email = $('#email').val().trim();
        const pass  = $('#pass').val();
        const conf  = $('#conf').val();

        if (!nom || !email || !pass) {
            alert("Por favor, completa los campos obligatorios.");
            return;
        }

        if (pass !== conf) {
            alert("Las contraseñas no coinciden.");
            return;
        }

        $('#btn-envio').hide();
        $('#loader').show();

        setTimeout(() => {
            $('#step-1').hide();
            $('#loader').hide();
            $('#step-2').show();
            $('#input-codigo').focus();
        }, 1500);
    };


    // --- 3. REGISTRO SIN BASE DE DATOS ---

    window.finalizarRegistro = function() {
        const codigoInput = $('#input-codigo').val().toUpperCase().trim();

        if (codigoInput === "SENA4") {

            // Guardar datos en localStorage (sin base de datos)
            const usuario = {
                nombre:   $('#nom').val(),
                apellido: $('#ape').val(),
                email:    $('#email').val(),
                telefono: $('#tel').val(),
                password: $('#pass').val()
            };

            localStorage.setItem('usuario_registrado', JSON.stringify(usuario));

            alert('¡Cuenta creada con éxito! Bienvenido/a, ' + usuario.nombre + '.');
            
            // LÍNEA 61: Redirigir al login tras éxito
            window.location.href = 'login.html';

        } else {
            alert('Código incorrecto. El código de prueba es: SENA4');
        }
    };

    // --- 4. NAVEGACIÓN ---
    
    // Función para el enlace "¿Ya tienes una cuenta?"
    window.irAlLogin = function() {
        window.location.href = 'login.html';
    };
});