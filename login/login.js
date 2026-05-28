// ── Panagpili ti bintana ti screen ──
function go(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
}

let contactoRecuperacion = '';
let metodoVerif = 'correo';

// ── Panagserrek ti User (Login) sadiay Database ──
function handleLogin() {
    const user = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-pass').value;
    const rol = document.getElementById('login-role').value;

    if (!user || !pass) {
        alert('⚠️ Pakisurat ti nagan ti user ken pasword-mo.');
        return;
    }

    const datos = new FormData();
    datos.append('usuario', user);
    datos.append('contrasena', pass);
    datos.append('rol', rol);

    // Panagpatulod iti login.php tapno maamuan no adda iti database
    fetch('login.php', {
        method: 'POST',
        body: datos
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert('✅ Maipalubos ti iseserrek: ' + data.msg);
            window.location.href = data.redirect; // Aquí PHP redirige de forma portable a la carpeta correcta
        } else {
            alert(data.msg);
        }
    })
    .catch(err => {
        console.error(err);
        alert('Adda biddut iti panagkonekta iti server.');
    });
}

// ── Panangisubli ti Pasword (Recuperación) ──
function enviarCodigo(metodo) {
    metodoVerif = metodo;
    const val = metodo === 'correo'
        ? document.getElementById('correo-input').value.trim()
        : document.getElementById('telefono-input').value.trim();

    if (!val) {
        alert('⚠️ Pakisuratan daytoy a blanko.');
        return;
    }

    contactoRecuperacion = val;

    const datos = new FormData();
    datos.append('accion', 'enviar_codigo');
    datos.append('metodo', metodo);
    datos.append('valor', val);

    // EDITADO: Cambiado 'recuperar.php' a 'recuperacion.php' para coincidir con nuestro controlador SQLite3
    fetch('recuperacion.php', {
        method: 'POST',
        body: datos
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const sub = document.getElementById('verif-subtitle');
            sub.textContent = metodo === 'correo'
                ? `Pakisurat ti kodigo a naipatulod sadiay ${val}`
                : `Pakisurat ti kodigo a naipatulod iti ${val}`;

            document.getElementById('codigo').value = '';
            document.getElementById('error-verif').style.display = 'none';
            go('screen-verificacion');
        } else {
            alert(data.msg);
        }
    })
    .catch(err => console.error(err));
}

// ── Beripikasion ti Kodigo ──
function verificarCodigo() {
    const ingresado = document.getElementById('codigo').value.trim().toUpperCase();
    const correcto = 'SENA4'; // Tu validación estática local e ideal para portabilidad offline

    if (ingresado === correcto) {
        go('screen-nueva-pass');
    } else {
        const err = document.getElementById('error-verif');
        err.style.display = 'block';
        setTimeout(() => { err.style.display = 'none'; }, 3000);
    }
}

// ── Panangipenpen iti Baro a Pasword sadiay DB ──
function guardarNuevaPassword() {
    const p1 = document.getElementById("p1").value;
    const p2 = document.getElementById("p2").value;
    const errorMsg = document.getElementById("error-pass");

    if (!p1 || !p2) {
        alert("⚠️ Pakisuratan amin a nasken a blanko.");
        return;
    }

    if (p1 !== p2) {
        errorMsg.style.display = "block";
        setTimeout(() => { errorMsg.style.display = "none"; }, 3000);
        return;
    }

    const datos = new FormData();
    datos.append('accion', 'actualizar_password');
    datos.append('metodo', metodoVerif);
    datos.append('valor', contactoRecuperacion);
    datos.append('password', p1); // Se envía en texto plano directo a SQLite3

    // EDITADO: Cambiado 'recuperar.php' a 'recuperacion.php' para apuntar al backend unificado de la clínica
    fetch('recuperacion.php', {
        method: 'POST',
        body: datos
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert("✅ Naibarion ti baro a pasword sadiay database ti CLINIDENT!");
            document.getElementById("p1").value = "";
            document.getElementById("p2").value = "";
            go('screen-login');
        } else {
            alert("Biddut: " + data.msg);
        }
    })
    .catch(err => console.error(err));
}

function irARegistro() {
    window.location.href = '../Registro/registro.html';
}

// Mantiene tu configuración de Service Worker (PWA portable) intacta
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(() => console.log('SW registrado'))
            .catch(err => console.log('Biddut SW:', err));
    });
}

