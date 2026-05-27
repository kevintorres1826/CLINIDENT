$(document).ready(function() {

    // --- 1. DAGITI FUNKSION TI INTERFAZ ---

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


    // --- 2. LOGIKA TI PANAGREHISTRO (PASO 1) ---

    window.simularEnvio = function() {
        const nom   = $('#nom').val().trim();
        const ape   = $('#ape').val().trim();
        const email = $('#email').val().trim();
        const tel   = $('#tel').val().trim();
        const pass  = $('#pass').val();
        const conf  = $('#conf').val();

        if (!nom || !ape || !email || !pass) {
            alert("Suroten ti rumbeng, pakisuratan amin a nasken a blanko.");
            return;
        }

        if (pass !== conf) {
            alert("Saan a nagpada dagiti pasword.");
            return;
        }

        $('#btn-envio').hide();
        $('#loader').show();

        // Paipatulod dagiti datos sadiay database babaen ti PHP
        $.post('registro.php', {
            nombre: nom,
            apellido: ape,
            email: email,
            telefono: tel,
            password: pass
        }, function(respuesta) {
            $('#loader').hide();
            if (respuesta.status === 'success') {
                $('#step-1').hide();
                $('#step-2').show();
                $('#input-codigo').focus();
            } else {
                alert("⚠️ Biddut: " + respuesta.msg);
                $('#btn-envio').show();
            }
        }, 'json').fail(function() {
            $('#loader').hide();
            $('#btn-envio').show();
            alert("Saan a makakonektar iti server.");
        });
    };


    // --- 3. PANAGREHISTRO SAYSAYAY ITI DATABASE (PASO 2) ---

    window.finalizarRegistro = function() {
        const codigoInput = $('#input-codigo').val().toUpperCase().trim();

        if (codigoInput === "SENA4") {
            alert('Nagballigi ti pannakaaramid ti kuentam sadiay CLINIDENT!');
            window.location.href = '../login/login.html';
        } else {
            alert('Saan a husto ti kodigo. Ti husto a kodigo ket: SENA4');
        }
    };

    // --- 4. PANAGNAYAGAR ---
    
    window.irAlLogin = function() {
        window.location.href ='../login/login.html';
    };
});