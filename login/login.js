// ── Cambiar de pantalla en la interfaz ──
function go(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
}

let contactoRecuperacion = '';
let metodoVerif = 'correo';

// ── Inicio de Sesión Automático ──
function handleLogin() {
    const user = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-pass').value;

    if (!user || !pass) {
        alert('⚠️ Por favor escribe tu correo y contraseña.');
        return;
    }

    const datos = new FormData();
    datos.append('usuario', user);
    datos.append('contrasena', pass);

    fetch('login.php', {
        method: 'POST',
        body: datos
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert('✅ Acceso permitido: ' + data.msg);
            window.location.href = data.redirect; 
        } else {
            alert(data.msg);
        }
    })
    .catch(err => {
        console.error(err);
        alert('Error al intentar conectar con el servidor local.');
    });
}

// ── Recuperación - Fase 1: Validar Existencia Real del Dato ──
function enviarCodigo(metodo) {
    metodoVerif = metodo;
    const val = metodo === 'correo'
        ? document.getElementById('correo-input').value.trim()
        : document.getElementById('telefono-input').value.trim();

    if (!val) {
        alert('⚠️ Por favor, llena este campo obligatorio.');
        return;
    }

    contactoRecuperacion = val;

    const datos = new FormData();
    datos.append('accion', 'enviar_codigo');
    datos.append('metodo', metodo);
    datos.append('valor', val);

    fetch('recuperacion.php', {
        method: 'POST',
        body: datos
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // El dato coincide en la base de datos, avanzamos de pantalla
            const sub = document.getElementById('verif-subtitle');
            sub.textContent = metodo === 'correo'
                ? `Escribe el código enviado a tu correo: ${val}`
                : `Escribe el código SMS enviado a tu teléfono: ${val}`;

            document.getElementById('codigo').value = '';
            document.getElementById('error-verif').style.display = 'none';
            go('screen-verificacion');
        } else {
            // ALERTA DE EQUIVOCACIÓN EN ESPAÑOL si el dato no existe registrado
            alert('❌ Error: ' + data.msg);
        }
    })
    .catch(err => {
        console.error(err);
        alert('Error al procesar la solicitud de recuperación.');
    });
}

// ── Recuperación - Fase 2: Validación del Código Local Maestro ──
function verificarCodigo() {
    const ingresado = document.getElementById('codigo').value.trim().toUpperCase();
    const correcto = 'SENA4'; 

    if (ingresado === correcto) {
        go('screen-nueva-pass');
    } else {
        // Alerta visual de código erróneo
        const err = document.getElementById('error-verif');
        err.innerText = "❌ Código incorrecto. Inténtalo de nuevo.";
        err.style.display = 'block';
        setTimeout(() => { err.style.display = 'none'; }, 3000);
    }
}

// ── Recuperación - Fase 3: Guardar Nueva Contraseña en la Base de Datos ──
function guardarNuevaPassword() {
    const p1 = document.getElementById("p1").value;
    const p2 = document.getElementById("p2").value;
    const errorMsg = document.getElementById("error-pass");

    // 1. Validar que no dejen los campos en blanco
    if (!p1 || !p2) {
        alert("⚠️ Por favor escribe y confirma tu nueva contraseña.");
        return;
    }

    // 2. Validar que ambas contraseñas coincidan
    if (p1 !== p2) {
        errorMsg.innerText = "❌ Las contraseñas ingresadas no coinciden.";
        errorMsg.style.display = "block";
        setTimeout(() => { errorMsg.style.display = "none"; }, 3000);
        return;
    }

    // 3. Empaquetar datos para enviarlos al PHP
    const datos = new FormData();
    datos.append('accion', 'actualizar_password');
    datos.append('metodo', metodoVerif); // 'correo' o 'telefono'
    datos.append('valor', contactoRecuperacion); // El correo/teléfono que se validó al inicio
    datos.append('password', p1); // La nueva clave

    // 4. Petición asíncrona al servidor
    fetch('recuperacion.php', {
        method: 'POST',
        body: datos
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert("✅ ¡Tu contraseña ha sido actualizada con éxito en el sistema!");
            document.getElementById("p1").value = "";
            document.getElementById("p2").value = "";
            go('screen-login'); // Redirige a la pantalla de login principal
        } else {
            alert("❌ Hubo un error: " + data.msg);
        }
    })
    .catch(err => console.error(err));
}

function irARegistro() {
    window.location.href = '../Registro/registro.html';
}

// Service Worker para la portabilidad offline
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(() => console.log('PWA: Service Worker Activo'))
            .catch(err => console.log('Error en SW:', err));
    });
}