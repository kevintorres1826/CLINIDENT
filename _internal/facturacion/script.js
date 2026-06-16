
/* ══════════════════════════════════════════════════════
   CLINIDENT – Facturación / script.js
══════════════════════════════════════════════════════ */
 
const API = 'http://127.0.0.1:5000';
 
let todasLasCitas    = [];
let citaSeleccionada = null;
let tratamientosOdo  = [];
let pagosLocales     = JSON.parse(localStorage.getItem('pagos_clinident')) || [];
let facturaActual    = null;
 
/* ══ MAPA: texto del panel_rec → nombre en tbltipotratamiento ════════════
   Las claves son los valores del <select id="tratamiento"> en panel_rec.html.
   Los valores son subcadenas del nombre en tbltipotratamiento (case-insensitive).
   Si el texto coincide parcialmente con el nombre del tipo, se autoselecciona. */
const MAPA_TRATAMIENTO = {
  'Limpieza Dental':  'limpieza',
  'Revisión General': 'consulta general',
  'Ortodoncia':       'ortodoncia',
  'Endodoncia':       'endodoncia',
  'Cirugía Oral':     'cirugía oral',
};
 
/* ══ INICIALIZACIÓN ═════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  cargarCitas();
  inicializarMetodosPago();
});
 
/* ══ CITAS ══════════════════════════════════════════ */
async function cargarCitas() {
  try {
    const res  = await fetch(`${API}/facturacion/citas-pendientes`, { credentials: 'include' });
    const data = await res.json();
    if (data.status !== 'success') throw new Error(data.message);
    todasLasCitas = data.citas;
    renderCitas(todasLasCitas);
  } catch (err) {
    document.getElementById('lista-citas').innerHTML = `
      <div class="empty-list">
        <p>⚠️ No se pudieron cargar las citas.<br><small>${err.message}</small></p>
        <button onclick="cargarCitas()" style="margin-top:12px;padding:8px 16px;border-radius:8px;
          background:#2563eb;color:white;border:none;cursor:pointer;font-weight:600;">
          Reintentar
        </button>
      </div>`;
  }
}
 
function renderCitas(citas) {
  const contenedor = document.getElementById('lista-citas');
 
  if (citas.length === 0) {
    contenedor.innerHTML = `<div class="empty-list"><p>✅ No hay citas pendientes de facturar.</p></div>`;
    return;
  }
 
  contenedor.innerHTML = citas.map(c => {
    // Mostrar el tratamiento agendado como badge si existe
    const badgeTratamiento = c.tratamiento
      ? `<span class="cita-tratamiento">💊 ${c.tratamiento}</span>`
      : '';
    return `
      <div class="cita-item" data-id="${c.id_cita}" onclick="seleccionarCita(${c.id_cita})">
        <div class="cita-fecha">
          ${formatFecha(c.fecha)} · ${c.hora_inicio.slice(0,5)}–${c.hora_fin.slice(0,5)}
        </div>
        <div class="cita-paciente">👤 ${c.nombre_paciente}</div>
        <div class="cita-doctor">🦷 ${c.nombre_odontologo}</div>
        <div class="cita-badges">
          <span class="cita-sala">📍 ${c.nombre_sala}</span>
          ${badgeTratamiento}
        </div>
      </div>`;
  }).join('');
}
 
function filtrarCitas() {
  const q = document.getElementById('buscador').value.toLowerCase();
  const filtradas = todasLasCitas.filter(c =>
    c.nombre_paciente.toLowerCase().includes(q) ||
    c.nombre_odontologo.toLowerCase().includes(q) ||
    c.nombre_sala.toLowerCase().includes(q) ||
    (c.tratamiento || '').toLowerCase().includes(q)
  );
  renderCitas(filtradas);
  if (citaSeleccionada) {
    document.querySelector(`.cita-item[data-id="${citaSeleccionada.id_cita}"]`)?.classList.add('seleccionada');
  }
}
 
async function seleccionarCita(id) {
  document.querySelectorAll('.cita-item').forEach(el => el.classList.remove('seleccionada'));
  document.querySelector(`.cita-item[data-id="${id}"]`)?.classList.add('seleccionada');
 
  citaSeleccionada = todasLasCitas.find(c => c.id_cita === id);
  if (!citaSeleccionada) return;
 
  // Resumen superior
  document.getElementById('cita-resumen').innerHTML = `
    <div class="resumen-campo">
      <span class="resumen-label">Paciente</span>
      <span class="resumen-valor">👤 ${citaSeleccionada.nombre_paciente}</span>
    </div>
    <div class="resumen-campo">
      <span class="resumen-label">Odontólogo</span>
      <span class="resumen-valor">🦷 ${citaSeleccionada.nombre_odontologo}</span>
    </div>
    <div class="resumen-campo">
      <span class="resumen-label">Fecha y Sala</span>
      <span class="resumen-valor">
        ${formatFecha(citaSeleccionada.fecha)} · ${citaSeleccionada.nombre_sala}
      </span>
    </div>
  `;
 
  document.getElementById('estado-vacio').classList.add('oculto');
  document.getElementById('form-factura').classList.remove('oculto');
 
  // Resetear campos de precio/descuento
  document.getElementById('diagnostico').value = '';
  document.getElementById('valor').value       = '';
  document.getElementById('descuento').value   = 0;
  document.getElementById('impuesto').value    = 0;
  calcularTotal();
 
  // Cargar tratamientos del odontólogo → luego autoseleccionar
  await cargarTratamientos(citaSeleccionada.id_odontologo, citaSeleccionada.tratamiento);
}
 
/* ══ TRATAMIENTOS ═══════════════════════════════════ */
async function cargarTratamientos(idOdo, tratamientoAgendado) {
  const select = document.getElementById('tipo-tratamiento');
  select.innerHTML = '<option value="">Cargando…</option>';
 
  try {
    const res  = await fetch(`${API}/facturacion/tratamientos-odontologo/${idOdo}`, { credentials: 'include' });
    const data = await res.json();
    if (data.status !== 'success') throw new Error(data.message);
 
    tratamientosOdo = data.tratamientos;
 
    select.innerHTML = '<option value="">Seleccione el procedimiento…</option>' +
      tratamientosOdo.map(t =>
        `<option value="${t.id_tipo}" data-precio="${t.precio_referencia}">${t.nombre}</option>`
      ).join('');
 
    // ── AUTOSELECCIÓN ─────────────────────────────────────────────────────
    if (tratamientoAgendado) {
      autoseleccionarTratamiento(select, tratamientoAgendado);
    }
 
  } catch (err) {
    select.innerHTML = '<option value="">Error al cargar tratamientos</option>';
    console.error(err);
  }
}
 
/**
 * Busca en el <select> la opción cuyo texto coincida mejor con
 * el tratamiento guardado al agendar la cita, y la selecciona.
 *
 * Estrategia (en orden de prioridad):
 *  1. Coincidencia exacta (case-insensitive)
 *  2. El valor del MAPA_TRATAMIENTO apunta a una subcadena del nombre del tipo
 *  3. El nombre del tipo contiene alguna palabra del tratamiento agendado
 */
function autoseleccionarTratamiento(select, tratamientoAgendado) {
  const agendadoLower = tratamientoAgendado.toLowerCase().trim();
 
  // Clave del mapa que puede estar asociada al texto guardado
  const subcadenaMapeo = MAPA_TRATAMIENTO[tratamientoAgendado]        // clave exacta
    ?? Object.entries(MAPA_TRATAMIENTO).find(([k]) =>
        agendadoLower.includes(k.toLowerCase())
      )?.[1];                                                          // clave parcial
 
  let mejorOpcion = null;
 
  for (const opt of select.options) {
    if (!opt.value) continue;
    const nombreTipo = opt.textContent.toLowerCase().trim();
 
    // Prioridad 1: texto exacto
    if (nombreTipo === agendadoLower) {
      mejorOpcion = opt;
      break;
    }
 
    // Prioridad 2: el mapa indica que este tipo corresponde al tratamiento
    if (subcadenaMapeo && nombreTipo.includes(subcadenaMapeo)) {
      mejorOpcion = opt;
      break;
    }
 
    // Prioridad 3: alguna palabra del tratamiento agendado aparece en el nombre del tipo
    if (!mejorOpcion) {
      const palabras = agendadoLower.split(/\s+/).filter(p => p.length > 3);
      if (palabras.some(p => nombreTipo.includes(p))) {
        mejorOpcion = opt;
        // No hacemos break: puede aparecer una coincidencia mejor después
      }
    }
  }
 
  if (mejorOpcion) {
    select.value = mejorOpcion.value;
    // Disparar el evento para que se autocomplete el precio
    actualizarPrecioReferencia();
 
    // Indicador visual de que fue autoseleccionado
    mostrarToast(`✨ Tratamiento autoseleccionado: ${mejorOpcion.textContent}`, 'ok');
  }
}
 
function actualizarPrecioReferencia() {
  const select = document.getElementById('tipo-tratamiento');
  const opt    = select.options[select.selectedIndex];
  const precio = parseFloat(opt?.dataset?.precio || 0);
  const hint   = document.getElementById('precio-ref');
 
  if (precio > 0) {
    hint.textContent = `Precio de referencia: ${formatCOP(precio)}`;
    if (!document.getElementById('valor').value) {
      document.getElementById('valor').value = precio;
      calcularTotal();
    }
  } else {
    hint.textContent = '';
  }
}
 
/* ══ CÁLCULO ════════════════════════════════════════ */
function calcularTotal() {
  const valor   = parseFloat(document.getElementById('valor').value)     || 0;
  const desc    = parseFloat(document.getElementById('descuento').value) || 0;
  const imp     = parseFloat(document.getElementById('impuesto').value)  || 0;
  const descVal = valor * (desc / 100);
  const base    = valor - descVal;
  const impVal  = base  * (imp  / 100);
  const total   = base  + impVal;
 
  document.getElementById('prev-subtotal').textContent  = formatCOP(valor);
  document.getElementById('prev-descuento').textContent = `-${formatCOP(descVal)}`;
  document.getElementById('prev-impuesto').textContent  = `+${formatCOP(impVal)}`;
  document.getElementById('prev-total').textContent     = formatCOP(total);
}
 
/* ══ EMITIR FACTURA ═════════════════════════════════ */
async function emitirFactura() {
  if (!citaSeleccionada) { mostrarToast('⚠️ Selecciona una cita primero', 'warn'); return; }
 
  const idTipo     = parseInt(document.getElementById('tipo-tratamiento').value);
  const diagnostico = document.getElementById('diagnostico').value.trim();
  const valor      = parseFloat(document.getElementById('valor').value);
  const descuento  = parseFloat(document.getElementById('descuento').value) || 0;
  const impuesto   = parseFloat(document.getElementById('impuesto').value)  || 0;
  const idMetodo   = parseInt(document.querySelector('input[name="metodo"]:checked').value);
 
  if (!idTipo)              { mostrarToast('⚠️ Selecciona un tipo de tratamiento', 'warn'); return; }
  if (!diagnostico)         { mostrarToast('⚠️ Escribe el diagnóstico', 'warn'); return; }
  if (!valor || valor <= 0) { mostrarToast('⚠️ Ingresa un valor mayor a 0', 'warn'); return; }
 
  const payload = {
    id_cita:        citaSeleccionada.id_cita,
    id_odontologo:  citaSeleccionada.id_odontologo,
    id_paciente:    citaSeleccionada.id_paciente,
    id_tipo:        idTipo,
    diagnostico,
    valor,
    descuento,
    impuesto,
    id_metodo_pago: idMetodo
  };
 
  try {
    const res  = await fetch(`${API}/facturacion/registrar`, {
      method:      'POST',
      credentials: 'include',
      headers:     { 'Content-Type': 'application/json' },
      body:        JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status !== 'success') throw new Error(data.message);
 
    const nombreTratamiento = document.getElementById('tipo-tratamiento')
      .options[document.getElementById('tipo-tratamiento').selectedIndex].text;
    const descVal = valor * (descuento / 100);
    const base    = valor - descVal;
    const impVal  = base  * (impuesto  / 100);
    const total   = base  + impVal;
 
    facturaActual = {
      id_factura:  data.id_factura,
      paciente:    citaSeleccionada.nombre_paciente,
      odontologo:  citaSeleccionada.nombre_odontologo,
      sala:        citaSeleccionada.nombre_sala,
      fecha_cita:  citaSeleccionada.fecha,
      tratamiento: nombreTratamiento,
      diagnostico,
      valor_base:  valor,
      descuento:   descVal,
      impuesto:    impVal,
      total,
      metodo:      ['', 'Tarjeta débito/crédito', 'Transferencia bancaria', 'Efectivo'][idMetodo]
    };
 
    pagosLocales.push(facturaActual);
    localStorage.setItem('pagos_clinident', JSON.stringify(pagosLocales));
 
    mostrarFacturaModal(facturaActual);
    mostrarToast('✅ Factura registrada con éxito', 'ok');
 
    todasLasCitas = todasLasCitas.filter(c => c.id_cita !== citaSeleccionada.id_cita);
    citaSeleccionada = null;
    renderCitas(todasLasCitas);
    document.getElementById('estado-vacio').classList.remove('oculto');
    document.getElementById('form-factura').classList.add('oculto');
 
  } catch (err) {
    mostrarToast(`❌ Error: ${err.message}`, 'error');
  }
}
 
/* ══ MODAL FACTURA ══════════════════════════════════ */
function mostrarFacturaModal(f) {
  document.getElementById('contenido-factura').innerHTML = `
    <div class="factura-header">
      <h2>CLINIDENT</h2>
      <p>Factura N.º ${f.id_factura}</p>
    </div>
    <div class="factura-grid">
      <div><strong>Paciente</strong><br>${f.paciente}</div>
      <div><strong>Odontólogo</strong><br>${f.odontologo}</div>
      <div><strong>Fecha cita</strong><br>${formatFecha(f.fecha_cita)}</div>
      <div><strong>Sala</strong><br>${f.sala}</div>
      <div><strong>Método de pago</strong><br>${f.metodo}</div>
      <div><strong>Fecha de emisión</strong><br>${new Date().toLocaleDateString('es-CO')}</div>
    </div>
    <table class="factura-tabla">
      <thead><tr><th>Tratamiento</th><th>Diagnóstico</th><th>Total</th></tr></thead>
      <tbody>
        <tr>
          <td>${f.tratamiento}</td>
          <td>${f.diagnostico}</td>
          <td>${formatCOP(f.total)}</td>
        </tr>
      </tbody>
    </table>
    <div class="factura-total">TOTAL PAGADO: ${formatCOP(f.total)}</div>
  `;
  document.getElementById('modal-factura').classList.add('visible');
}
 
function cerrarModal() {
  document.getElementById('modal-factura').classList.remove('visible');
}
 
/* ══ HISTORIAL DE PAGOS ═════════════════════════════ */
function verPagos() {
  let html = `<h2 style="margin-bottom:14px">📂 Historial de facturas</h2>`;
 
  if (pagosLocales.length === 0) {
    html += `<p style="color:var(--muted)">No hay facturas registradas en esta sesión.</p>`;
  } else {
    html += `<table class="tabla-pagos">
      <thead><tr><th>#</th><th>Paciente</th><th>Tratamiento</th><th>Total</th></tr></thead><tbody>`;
    pagosLocales.forEach(p => {
      html += `<tr>
        <td>${p.id_factura}</td>
        <td>${p.paciente}</td>
        <td>${p.tratamiento}</td>
        <td>${formatCOP(p.total)}</td>
      </tr>`;
    });
    html += `</tbody></table>`;
  }
 
  document.getElementById('contenido-pagos').innerHTML = html;
  document.getElementById('modal-pagos').classList.add('visible');
}
 
/* ══ MÉTODOS DE PAGO – UI ═══════════════════════════ */
function inicializarMetodosPago() {
  document.querySelectorAll('.metodo-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.metodo-card').forEach(c => c.classList.remove('activo'));
      card.classList.add('activo');
      card.querySelector('input').checked = true;
    });
  });
}
 
/* ══ UTILIDADES ═════════════════════════════════════ */
function formatFecha(iso) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  const meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  return `${parseInt(d)} ${meses[parseInt(m)-1]} ${y}`;
}
 
function formatCOP(n) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n || 0);
}
 
let toastTimeout;
function mostrarToast(msg, tipo = 'ok') {
  let toast = document.getElementById('toast-global');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-global';
    toast.style.cssText = `
      position:fixed; bottom:90px; right:28px; padding:12px 20px;
      border-radius:12px; font-weight:600; font-size:14px; z-index:9999;
      box-shadow:0 8px 24px rgba(0,0,0,.2); transition:opacity .3s;
      font-family:'Plus Jakarta Sans',sans-serif;
    `;
    document.body.appendChild(toast);
  }
  const colores = { ok: '#16a34a', warn: '#d97706', error: '#dc2626' };
  toast.style.background = colores[tipo] || colores.ok;
  toast.style.color  = 'white';
  toast.style.opacity = '1';
  toast.textContent  = msg;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { toast.style.opacity = '0'; }, 3500);
}
 