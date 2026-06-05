// ==========================================
// ── 1. MOTOR DE CAMBIO DE PANTALLAS ──
// ==========================================
function go(screenId) {
    document.querySelectorAll('.forms-panel .screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
}

// Alternar entre el flujo de Login y Registro desde el Panel Fijo
let modoActual = "login"; 

function alternarFormularios() {
    const title = document.getElementById('welcome-title');
    const text = document.getElementById('welcome-text');
    const label = document.getElementById('toggle-label');
    const button = document.getElementById('btn-switch');

    if (modoActual === "login") {
        modoActual = "registro";
        title.innerText = "¡Únete a Clinident!";
        text.innerText = "Regístrate hoy mismo para agendar tus citas en línea de forma ágil y segura.";
        label.innerText = "¿Ya tienes una cuenta?";
        button.innerText = "Iniciar Sesión";
        
        // Limpieza preventiva de jQuery
        $('#step-2').hide();
        $('#step-1').show(); 
        $('#btn-envio').show();
        $('#loader').hide();
        
        go('step-1'); 
    } else {
        modoActual = "login";
        title.innerText = "¡Bienvenido de nuevo!";
        text.innerText = "Accede a tu panel clínico para gestionar tus citas, tratamientos e historial médico premium.";
        label.innerText = "¿No tienes una cuenta?";
        button.innerText = "Registrarse aquí";
        go('screen-login'); 
    }
}

// ==========================================
// ── 2. MÓDULO LOGIN & RECUPERACIÓN (Python) ──
// ==========================================
let contactoRecuperacion = '';
let metodoVerif = 'correo'; // 👈 Declarada una única vez aquí de manera global

function handleLogin() {
    const user = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-pass').value;

    if (!user || !pass) {
        alert('⚠️ Por favor escribe tu correo y contraseña.');
        return;
    }

    // CONTROL ANTIFALLOS: urlBase blindada por si config.js no responde a tiempo
    const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : "http://127.0.0.1:5000";

    const datos = new FormData();
    datos.append('usuario', user);
    datos.append('contrasena', pass);

    fetch(`${urlBase}/login/login`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(Object.fromEntries(datos)) 
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert("¡Inicio de sesión correcto!");
            window.location.href = "../agenda_cliente/index.html"; 
        } else {
            const mensajeError = data.message || data.msg || "Credenciales incorrectas o error interno.";
            alert("Error: " + mensajeError);
        }
    })
    .catch(error => {
        console.error("Error en la petición:", error);
        alert("Error al intentar conectar con el servidor local.");
    });
} 

function seleccionarMetodo(tipo) {
    metodoVerif = tipo;
    const titulo = document.getElementById('titulo-dato');
    const sub = document.getElementById('sub-dato');
    const label = document.getElementById('label-dinamico');
    const input = document.getElementById('input-recuperacion');

    if (tipo === 'correo') {
        titulo.innerText = "Recuperar por Correo";
        sub.innerText = "Enviaremos un código a tu dirección electrónica registrada.";
        label.innerText = "Correo Electrónico";
        input.placeholder = "ejemplo@correo.com";
        input.type = "email";
    } else {
        titulo.innerText = "Recuperar por Celular";
        sub.innerText = "Enviaremos un código SMS a tu número telefónico registrado.";
        label.innerText = "Número de Teléfono";
        input.placeholder = "3001234567";
        input.type = "text";
    }
    input.value = "";
    go('screen-ingresar-dato');
}

function enviarCodigoVerificacion() {
    const valorInput = document.getElementById('input-recuperacion').value.trim();
    if (!valorInput) {
        alert("⚠️ Por favor ingresa el dato solicitado.");
        return;
    }
    contactoRecuperacion = valorInput;

    const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : "http://127.0.0.1:5000";

    const datos = new FormData();
    datos.append('accion', 'enviar_codigo');
    datos.append('metodo', metodoVerif);
    datos.append('valor', contactoRecuperacion);

    fetch(`${urlBase}/login/recuperacion`, { 
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(Object.fromEntries(datos))
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert("📩 Código enviado. Por seguridad, el código de validación es: 123456");
            document.getElementById('verif-subtitle').innerText = `Ingresa el código enviado a tu ${metodoVerif === 'correo' ? 'correo' : 'teléfono'}`;
            document.getElementById('codigo').value = "";
            go('screen-verificacion');
        } else {
            alert("❌ " + (data.message || data.msg));
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error al conectar con el servicio de recuperación.");
    });
}

function verificarCodigo() {
    const cod = document.getElementById('codigo').value.trim();
    if (cod === "123456") {
        document.getElementById('error-verif').style.display = "none";
        document.getElementById('p1').value = "";
        document.getElementById('p2').value = "";
        go('screen-nueva-pass');
    } else {
        document.getElementById('error-verif').style.display = "block";
    }
}

function guardarNuevaPassword() {
    const p1 = document.getElementById('p1').value;
    const p2 = document.getElementById('p2').value;
    const errorMsg = document.getElementById('error-pass');

    if (!p1 || !p2) {
        alert("⚠️ Por favor completa ambos campos de contraseña.");
        return;
    }

    if (p1 !== p2) {
        errorMsg.style.display = "block";
        setTimeout(() => { errorMsg.style.display = "none"; }, 3000);
        return;
    }

    const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : "http://127.0.0.1:5000";

    const datos = new FormData();
    datos.append('accion', 'actualizar_password');
    datos.append('metodo', metodoVerif);
    datos.append('valor', contactoRecuperacion);
    datos.append('password', p1);

    fetch(`${urlBase}/login/recuperacion`, { 
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(Object.fromEntries(datos))
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert("✅ ¡Tu contraseña ha sido actualizada con éxito en el sistema!");
            go('screen-login');
        } else {
            alert("❌ Hubo un error: " + (data.message || data.msg));
        }
    })
    .catch(err => console.error(err));
}

// ==========================================
// ── 3. MÓDULO LOGIC REGISTRO (jQuery) ──
// ==========================================
$(document).ready(function() {
    // Visibilidad de contraseñas
    $(document).on('click', '.toggle-password', function() {
        const input = $('#pass');
        if (input.attr('type') === "password") {
            input.attr('type', 'text');
            $(this).removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            $(this).removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });

    window.abrirModal = function() { $('#modalLegal').css('display', 'flex'); };
    window.cerrarModal = function() { $('#modalLegal').hide(); };
    
    window.validarBoton = function() {
        const estaChequeado = $('#acepto-datos').is(':checked');
        $('#btn-envio').prop('disabled', !estaChequeado);
    };

    window.simularEnvio = function() {
        const nom   = $('#nom').val().trim();
        const ape   = $('#ape').val().trim();
        const email = $('#email').val().trim();
        const tel   = $('#tel').val().trim();
        const pass  = $('#pass').val();

        if (!nom || !ape || !email || !pass) {
            alert("⚠️ Por favor rellena todos los campos obligatorios.");
            return;
        }

        $('#btn-envio').hide();
        $('#loader').show();

        const datosRegistro = {
            nombre: nom,
            apellido: ape,
            email: email,
            telefono: tel,
            password: pass
        };

        const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : "http://127.0.0.1:5000";

        fetch(`${urlBase}/Registro/registro`, { 
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datosRegistro)
        })
        .then(res => res.json())
        .then(respuesta => {
            $('#loader').hide();
            if (respuesta.status === 'success') {
                $('#step-1').hide();
                $('#step-2').show();
                go('step-2'); 
                $('#input-codigo').focus();
            } else {
                alert("⚠️ Error: " + (respuesta.message || respuesta.msg));
                $('#btn-envio').show();
            }
        })
        .catch(function() {
            $('#loader').hide();
            $('#btn-envio').show();
            alert("Error al enviar los datos. Por favor, inténtalo de nuevo.");
        });
    };

    window.finalizarRegistro = function() {
        const codigoInput = $('#input-codigo').val().toUpperCase().trim();
        const nom = $('#nom').val().trim(); 
        
        if (codigoInput === "SENA4") {
            alert('🎉 ¡Tu cuenta ha sido creada exitosamente! Bienvenido a Clinident.');
            
            if (nom) {
                localStorage.setItem('clinident_usuario_nombre', nom);
            }
            
            // Limpieza de campos post-registro
            $('#nom').val('');
            $('#ape').val('');
            $('#email').val('');
            $('#tel').val('');
            $('#pass').val('');
            $('#input-codigo').val('');
            $('#acepto-datos').prop('checked', false);
            
            $('#step-2').hide();
            $('#step-1').show();
            $('#btn-envio').prop('disabled', true).show(); 
            
            window.location.href = '../agenda_cliente/index.html';
            
        } else {
            alert('❌ Código incorrecto (El código en esta versión de prueba es: SENA4)');
        }
    };
});