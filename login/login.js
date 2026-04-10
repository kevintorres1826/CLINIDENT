// ── Navegación entre pantallas ──
function go(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
}

// ── Manejo de Login ──
function handleLogin() {
    const user = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-pass').value;
    const rol = document.getElementById('login-role').value;

    if (!user || !pass) {
        alert('⚠️ Por favor escribe tu usuario y contraseña');
        return;
    }

    // Lógica de redirección por rol
    const rutas = {
        paciente:'../agenda cliente/index.html',
        odontologo:'../odontologo/panel_medico.html',
        admin: '../odontologo/panel_medico.html',
        recepcion: '../odontologo/panel_medico.html',
    };
    
    window.location.href = rutas[rol] || 'odontologo.html';
}

// ── Recuperación de Contraseña ──
let metodoVerif = 'correo';

function enviarCodigo(metodo) {
    metodoVerif = metodo;
    const val = metodo === 'correo'
        ? document.getElementById('correo-input').value.trim()
        : document.getElementById('telefono-input').value.trim();

    if (!val) {
        alert('⚠️ Por favor completa el campo');
        return;
    }

    const sub = document.getElementById('verif-subtitle');
    sub.textContent = metodo === 'correo'
        ? `Ingresa el código enviado a ${val}`
        : `Ingresa el código enviado al ${val}`;

    // Limpiar y navegar
    document.getElementById('codigo').value = '';
    document.getElementById('error-verif').style.display = 'none';
    go('screen-verificacion');
}

// ── Verificación de Código ──
function verificarCodigo() {
    // Convertimos a mayúsculas para que acepte "sena4" o "SENA4"
    const ingresado = document.getElementById('codigo').value.trim().toUpperCase();
    const correcto = 'SENA4'; 

    if (ingresado === correcto) {
        // Al ser correcto, navegamos a la pantalla de nueva contraseña
        go('screen-nueva-pass');
    } else {
        const err = document.getElementById('error-verif');
        err.style.display = 'block';
        setTimeout(() => { err.style.display = 'none'; }, 3000);
    }
}

// ── NUEVA FUNCIÓN: Guardar Nueva Contraseña ──
function guardarNuevaPassword() {
    const p1 = document.getElementById("p1").value;
    const p2 = document.getElementById("p2").value;
    const errorMsg = document.getElementById("error-pass");

    // Validación de campos vacíos
    if (!p1 || !p2) {
        alert("⚠️ Por favor completa ambos campos");
        return;
    }

    // Validación de coincidencia
    if (p1 !== p2) {
        errorMsg.style.display = "block";
        setTimeout(() => { errorMsg.style.display = "none"; }, 3000);
        return;
    }

    // Simulación de éxito
    alert("✅ ¡Contraseña actualizada con éxito!");
    
    // Limpiar campos y volver al login
    document.getElementById("p1").value = "";
    document.getElementById("p2").value = "";
    go('screen-login');
}

function irARegistro() {
    window.location.href = '../Registro/registro.html';
}

// ── Registro de Service Worker (PWA) ──
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(() => console.log('SW registrado con éxito'))
            .catch(err => console.log('Error al registrar SW:', err));
    });
}