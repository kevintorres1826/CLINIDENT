
// ==========================================
// ── VARIABLES GLOBALES ──
// ==========================================
let mode = 'login';
let recovMet = 'correo';
let recovContact = '';
 
// ==========================================
// ── SPLASH SCREEN ──
// ==========================================
(function splash() {
  const bar = document.getElementById('sbar');
  const lbl = document.getElementById('slabel');
  const msgs = ['Cargando sistema...', 'Conectando servidor...', 'Preparando portal...', '¡Listo!'];
  let pct = 0, step = 0;
 
  const iv = setInterval(() => {
    pct += Math.random() * 18 + 5;
    if (pct >= 100) {
      pct = 100;
      clearInterval(iv);
      setTimeout(() => {
        document.getElementById('splash').classList.add('hide');
      }, 500);
    }
    bar.style.width = Math.min(pct, 100) + '%';
    const si = Math.floor((pct / 100) * msgs.length);
    if (si < msgs.length && si !== step) {
      step = si;
      lbl.textContent = msgs[si];
    }
  }, 220);
})();
 
// ==========================================
// ── INDICADOR DE COINCIDENCIA DE CONTRASEÑAS ──
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  const p1   = document.getElementById('r-pass');
  const p2   = document.getElementById('r-pass2');
  const hint = document.getElementById('pass-hint');
 
  function checkMatch() {
    if (!p2.value) { hint.textContent = ''; hint.className = 'pass-hint'; return; }
    if (p1.value === p2.value) {
      hint.textContent = '✔ Las contraseñas coinciden';
      hint.className   = 'pass-hint match';
    } else {
      hint.textContent = '✖ Las contraseñas no coinciden';
      hint.className   = 'pass-hint nomatch';
    }
  }
 
  p1.addEventListener('input', checkMatch);
  p2.addEventListener('input', checkMatch);
});
 
// ==========================================
// ── TRANSICIÓN LOGIN ↔ REGISTRO ──
// ==========================================
function toggleMode() {
  const sh2    = document.getElementById('sh2');
  const sp     = document.getElementById('sp');
  const hint   = document.getElementById('sw-hint');
  const btn    = document.getElementById('btn-sw');
  const slider = document.getElementById('slider');
 
  if (mode === 'login') {
    mode = 'reg';
    sh2.textContent  = '¡Únete a Clinident!';
    sp.textContent   = 'Regístrate para gestionar tus citas de forma ágil y segura.';
    hint.textContent = '¿Ya tienes una cuenta?';
    btn.textContent  = 'Iniciar sesión';
    slider.classList.add('to-reg');
  } else {
    mode = 'login';
    sh2.textContent  = '¡Bienvenido de nuevo!';
    sp.textContent   = 'Accede a tu historial, citas y tratamientos desde un solo lugar.';
    hint.textContent = '¿No tienes cuenta?';
    btn.textContent  = 'Registrarse aquí';
    slider.classList.remove('to-reg');
  }
}
 
// ==========================================
// ── TABS: LOGIN / RECUPERACIÓN ──
// ==========================================
function showLoginTab(t) {
  const vl  = document.getElementById('v-login');
  const vr  = document.getElementById('v-recov');
  const tl  = document.getElementById('tab-login');
  const tr  = document.getElementById('tab-recov');
  const bar = document.getElementById('tab-bar');
 
  if (t === 'login') {
    vl.style.display = '';
    vr.style.display = 'none';
    tl.classList.add('active');
    tr.classList.remove('active');
    bar.style.left = '0%';
  } else {
    vl.style.display = 'none';
    vr.style.display = '';
    tl.classList.remove('active');
    tr.classList.add('active');
    bar.style.left = '50%';
  }
}
 
// ==========================================
// ── OJO CONTRASEÑA ──
// ==========================================
function eye(id, btn) {
  const inp = document.getElementById(id);
  const ico = btn.querySelector('i');
  if (inp.type === 'password') {
    inp.type      = 'text';
    ico.className = 'ti ti-eye-off';
  } else {
    inp.type      = 'password';
    ico.className = 'ti ti-eye';
  }
}
 
// ==========================================
// ── RATE LIMITING: temporizador visual ──
// ==========================================
let _timerInterval = null;
 
function activarTemporizador(segundos) {
  const btn = document.getElementById('btn-login');
  if (!btn) return;
 
  // Cancelar temporizador previo si lo hubiera
  if (_timerInterval) clearInterval(_timerInterval);
 
  btn.disabled = true;
  let t = segundos;
  btn.textContent = `Bloqueado (${t}s)`;
 
  _timerInterval = setInterval(() => {
    t--;
    if (t <= 0) {
      clearInterval(_timerInterval);
      _timerInterval      = null;
      btn.disabled        = false;
      btn.textContent     = 'Ingresar';
 
      // Ocultar mensaje de error cuando se levanta el bloqueo
      const errEl = document.getElementById('login-error');
      if (errEl) errEl.style.display = 'none';
    } else {
      btn.textContent = `Bloqueado (${t}s)`;
    }
  }, 1000);
}
 
function mostrarErrorLogin(msg) {
  // Muestra el mensaje en el elemento #login-error si existe,
  // de lo contrario usa alert como fallback.
  const errEl = document.getElementById('login-error');
  if (errEl) {
    errEl.textContent    = msg;
    errEl.style.display  = 'block';
  } else {
    alert(msg);
  }
}
 
// ==========================================
// ── LOGIN ──
// ==========================================
function doLogin() {
  const u = document.getElementById('l-user').value.trim();
  const p = document.getElementById('l-pass').value;
 
  if (!u || !p) {
    mostrarErrorLogin('⚠ Escribe tu correo y contraseña.');
    return;
  }
 
  const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://127.0.0.1:5000';
 
  fetch(`${urlBase}/login/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usuario: u, contrasena: p })
  })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'success') {
        window.location.href = d.redirect;
      } else {
        mostrarErrorLogin(d.msg || d.message || '⚠ Credenciales incorrectas.');
 
        // Si el servidor indicó bloqueo, iniciar cuenta regresiva
        if (d.bloqueado && d.tiempo_restante) {
          activarTemporizador(d.tiempo_restante);
 
          // Mostrar proactivamente el enlace de recuperar contraseña
          const enlaceRecuperar = document.getElementById('enlace-recuperar');
          if (enlaceRecuperar) enlaceRecuperar.style.display = 'block';
        }
      }
    })
    .catch(() => mostrarErrorLogin('❌ No se pudo conectar con el servidor.'));
}
 
// ==========================================
// ── RECUPERACIÓN ──
// ==========================================
function selRecov(m) {
  recovMet = m;
  document.getElementById('rv-opts').style.display = 'none';
  document.getElementById('rv-dato').style.display = '';
 
  const isEmail = m === 'correo';
  document.getElementById('rv-title').textContent = isEmail ? 'Recuperar por correo' : 'Recuperar por celular';
  document.getElementById('rv-sub').textContent   = isEmail ? 'Escribe tu correo registrado' : 'Escribe tu número registrado';
  document.getElementById('rv-lbl').textContent   = isEmail ? 'Correo' : 'Celular';
 
  const inp = document.getElementById('rv-inp');
  inp.type        = isEmail ? 'email' : 'text';
  inp.placeholder = isEmail ? 'ejemplo@correo.com' : '3001234567';
  inp.value       = '';
 
  document.getElementById('rv-ico').className = (isEmail ? 'ti ti-mail' : 'ti ti-device-mobile') + ' ico';
}
 
function sendRecov() {
  const val = document.getElementById('rv-inp').value.trim();
  if (!val) { alert('⚠ Ingresa el dato solicitado.'); return; }
  recovContact = val;
 
  const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://127.0.0.1:5000';
 
  fetch(`${urlBase}/login/recuperacion`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accion: 'enviar_codigo', metodo: recovMet, valor: val })
  })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'success') {
        alert('📩 Código enviado. (Demo: el código es 123456)');
        document.getElementById('rv-vsub').textContent  = `Código enviado a tu ${recovMet === 'correo' ? 'correo' : 'celular'}`;
        document.getElementById('rv-dato').style.display   = 'none';
        document.getElementById('rv-code').value           = '';
        document.getElementById('rv-err').style.display    = 'none';
        document.getElementById('rv-verif').style.display  = '';
      } else {
        alert('❌ ' + (d.message || d.msg));
      }
    })
    .catch(() => alert('❌ No se pudo conectar con el servidor.'));
}
 
function verifyRecov() {
  const cod = document.getElementById('rv-code').value.trim();
  const err = document.getElementById('rv-err');
 
  if (cod === '123456') {
    err.style.display                                   = 'none';
    document.getElementById('rv-verif').style.display  = 'none';
    document.getElementById('rv-newpass').style.display = '';
    document.getElementById('np1').value               = '';
    document.getElementById('np2').value               = '';
  } else {
    err.style.display = 'block';
  }
}
 
function saveNewPass() {
  const p1  = document.getElementById('np1').value;
  const p2  = document.getElementById('np2').value;
  const err = document.getElementById('np-err');
 
  if (!p1 || !p2) { alert('⚠ Completa ambos campos.'); return; }
  if (p1 !== p2) {
    err.style.display = 'block';
    setTimeout(() => err.style.display = 'none', 3000);
    return;
  }
  err.style.display = 'none';
 
  const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://127.0.0.1:5000';
 
  fetch(`${urlBase}/login/recuperacion`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accion: 'actualizar_password', metodo: recovMet, valor: recovContact, password: p1 })
  })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'success') {
        alert('✅ ¡Contraseña actualizada con éxito!');
        document.getElementById('rv-newpass').style.display = 'none';
        document.getElementById('rv-opts').style.display    = '';
        showLoginTab('login');
      } else {
        alert('❌ Error: ' + (d.message || d.msg));
      }
    })
    .catch(() => {});
}
 
// ==========================================
// ── REGISTRO ──
// ==========================================
function doReg() {
  const nom   = document.getElementById('r-nom').value.trim();
  const ape   = document.getElementById('r-ape').value.trim();
  const email = document.getElementById('r-email').value.trim();
  const tel   = document.getElementById('r-tel').value.trim();
  const pass  = document.getElementById('r-pass').value;
  const pass2 = document.getElementById('r-pass2').value;
 
  // ── 1. Validaciones Frontend (Rápidas) ──
  if (!nom || !ape || !email || !tel || !pass) {
    alert('⚠ Por favor rellena todos los campos obligatorios.');
    return;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    alert('⚠ El correo no tiene un formato válido (debe contener "@" y un dominio).');
    document.getElementById('r-email').focus();
    return;
  }
  if (!/^\d{10}$/.test(tel)) {
    alert('⚠ El celular debe tener exactamente 10 dígitos numéricos.');
    document.getElementById('r-tel').focus();
    return;
  }
  if (pass !== pass2) {
    alert('⚠ Las contraseñas no coinciden. Verifícalas antes de continuar.');
    document.getElementById('r-pass2').focus();
    return;
  }
  if (pass.length < 8) {
    alert('⚠ La contraseña debe tener al menos 8 caracteres.');
    document.getElementById('r-pass').focus();
    return;
  }
  if (!/[A-Z]/.test(pass)) {
    alert('⚠ La contraseña debe contener al menos una letra mayúscula.');
    document.getElementById('r-pass').focus();
    return;
  }
  if (!/[a-z]/.test(pass)) {
    alert('⚠ La contraseña debe contener al menos una letra minúscula.');
    document.getElementById('r-pass').focus();
    return;
  }
  if (!/[!"#$%&'()*+,.\/:;<=>?@[\]\\^_`{|}~-]/.test(pass)) {
    alert('⚠ La contraseña debe contener al menos un carácter especial.');
    document.getElementById('r-pass').focus();
    return;
  }
 
  // ── 2. Mostrar Loader ──
  document.getElementById('btn-reg').style.display   = 'none';
  document.getElementById('reg-loader').style.display = 'flex';
 
  const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://127.0.0.1:5000';
 
  // ── 3. Petición al Backend (Python) ──
  fetch(`${urlBase}/Registro/registro`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre: nom, apellido: ape, email, telefono: tel, password: pass, confirmar: pass2 })
  })
    .then(r => r.json()) // Lee el JSON UNA SOLA VEZ
    .then(d => {
      // Ocultar Loader
      document.getElementById('reg-loader').style.display = 'none';
 
      if (d.status === 'success') {
        // Todo perfecto: avanzamos de paso.
        // IMPORTANTE: en este punto el backend NO ha guardado nada en la BD,
        // solo dejó los datos pendientes en sesión. Falta verificar el código.
        document.getElementById('r-code').value = '';
        document.getElementById('reg-slider').classList.add('to-step2');
      } else {
        // Error de validación en Python (ej. faltan mayúsculas, correo duplicado, etc.)
        alert('⚠ ' + (d.message || d.msg));
        document.getElementById('btn-reg').style.display = 'flex';
      }
    })
    .catch((error) => {
      // Esto solo pasa si se cae el internet o Python falla gravemente
      document.getElementById('reg-loader').style.display = 'none';
      document.getElementById('btn-reg').style.display    = 'flex';
      alert('❌ Error al enviar los datos. Revisa la conexión con el servidor.');
      console.error(error);
    });
}
 
function finishReg() {
  const cod   = document.getElementById('r-code').value.toUpperCase().trim();
  const nom   = document.getElementById('r-nom').value.trim();
  const email = document.getElementById('r-email').value.trim();
 
  if (!cod) {
    alert('⚠ Ingresa el código de verificación.');
    return;
  }
 
  const urlBase = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://127.0.0.1:5000';
 
  // La cuenta SOLO se crea en la base de datos si el backend confirma
  // que el código es correcto. Hasta este punto, nada se ha guardado.
  fetch(`${urlBase}/Registro/verificar`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, codigo: cod })
  })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'success') {
        alert('🎉 ¡Cuenta creada exitosamente! Bienvenido a Clinident.');
        if (nom) localStorage.setItem('clinident_usuario_nombre', nom);
 
        ['r-nom', 'r-ape', 'r-email', 'r-tel', 'r-pass', 'r-pass2', 'r-code'].forEach(id => {
          document.getElementById(id).value = '';
        });
        document.getElementById('pass-hint').textContent  = '';
        document.getElementById('r-ok').checked           = false;
        document.getElementById('btn-reg').disabled       = true;
        document.getElementById('btn-reg').style.display  = 'flex';
        document.getElementById('reg-slider').classList.remove('to-step2');
 
        window.location.href = '../agenda_cliente/index.html';
      } else {
        // Código incorrecto o sesión pendiente vencida/inexistente
        alert('❌ ' + (d.msg || d.message || 'Código incorrecto. (Demo: SENA4)'));
      }
    })
    .catch(() => alert('❌ No se pudo conectar con el servidor.'));
}
 
// ==========================================
// ── MODAL PRIVACIDAD ──
// ==========================================
function openModal() {
  document.getElementById('modal').classList.add('open');
}
 
function closeModal() {
  document.getElementById('modal').classList.remove('open');
}
 