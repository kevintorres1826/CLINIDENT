
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
 
  document.getElementById('diagnostico').value  = '';
  document.getElementById('precio-base').value  = '';
  document.getElementById('cobro-extra').value  = '';
 
  /* Resetear sección efectivo al cambiar de cita */
  document.getElementById('monto-recibido').value = '';
  document.getElementById('valor-cambio').textContent = formatCOP(0);
  document.getElementById('seccion-efectivo').style.display = 'none';
 
  calcularTotal();
 
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
        `<option value="${t.id_tipo}" data-precio="${t.precio_base}">${t.nombre}</option>`
      ).join('');
 
    if (tratamientoAgendado) {
      autoseleccionarTratamiento(select, tratamientoAgendado);
    }
 
  } catch (err) {
    select.innerHTML = '<option value="">Error al cargar tratamientos</option>';
    console.error(err);
  }
}
 
function autoseleccionarTratamiento(select, tratamientoAgendado) {
  const agendadoLower = tratamientoAgendado.toLowerCase().trim();
 
  const subcadenaMapeo = MAPA_TRATAMIENTO[tratamientoAgendado]
    ?? Object.entries(MAPA_TRATAMIENTO).find(([k]) =>
        agendadoLower.includes(k.toLowerCase())
      )?.[1];
 
  let mejorOpcion = null;
 
  for (const opt of select.options) {
    if (!opt.value) continue;
    const nombreTipo = opt.textContent.toLowerCase().trim();
 
    if (nombreTipo === agendadoLower) {
      mejorOpcion = opt;
      break;
    }
 
    if (subcadenaMapeo && nombreTipo.includes(subcadenaMapeo)) {
      mejorOpcion = opt;
      break;
    }
 
    if (!mejorOpcion) {
      const palabras = agendadoLower.split(/\s+/).filter(p => p.length > 3);
      if (palabras.some(p => nombreTipo.includes(p))) {
        mejorOpcion = opt;
      }
    }
  }
 
  if (mejorOpcion) {
    select.value = mejorOpcion.value;
    actualizarPrecioReferencia();
    mostrarToast(`✨ Tratamiento autoseleccionado: ${mejorOpcion.textContent}`, 'ok');
  }
}
 
function actualizarPrecioReferencia() {
  const select = document.getElementById('tipo-tratamiento');
  const opt    = select.options[select.selectedIndex];
  const precio = parseFloat(opt?.dataset?.precio || 0);
  document.getElementById('precio-base').value = precio || '';
  document.getElementById('cobro-extra').value = '';
  calcularTotal();
}
 
/* ══ CÁLCULO ════════════════════════════════════════ */
function calcularTotal() {
  const base  = parseFloat(document.getElementById('precio-base').value)  || 0;
  const extra = parseFloat(document.getElementById('cobro-extra').value) || 0;
  
  const subtotal = base + extra;
  
  const aplicarIva = document.getElementById('aplicar-iva').checked;
  const tarifaIva  = aplicarIva ? 0.19 : 0;
  const valorIva   = subtotal * tarifaIva;
  
  const total = subtotal + valorIva;
  
  document.getElementById('prev-base').textContent  = formatCOP(base);
  document.getElementById('prev-extra').textContent = `+${formatCOP(extra)}`;
  document.getElementById('prev-iva').textContent   = `+${formatCOP(valorIva)}`;
  document.getElementById('prev-total').textContent = formatCOP(total);
 
  /* Recalcular cambio si el método activo es efectivo */
  calcularCambio();
}
 
/* ══ CAMBIO EN EFECTIVO ══════════════════════════════ */
function calcularCambio() {
  const base      = parseFloat(document.getElementById('precio-base').value) || 0;
  const extra     = parseFloat(document.getElementById('cobro-extra').value) || 0;
  const iva       = document.getElementById('aplicar-iva').checked ? 0.19 : 0;
  const total     = (base + extra) * (1 + iva);

  const recibido   = parseFloat(document.getElementById('monto-recibido').value) || 0;
  const diferencia = recibido - total;

  const elCambio = document.getElementById('valor-cambio');

  if (recibido === 0) {
    elCambio.textContent = formatCOP(0);
    elCambio.classList.remove('insuficiente');
    return;
  }

  if (diferencia < 0) {
    elCambio.textContent = `⚠️ Faltan ${formatCOP(Math.abs(diferencia))}`;
    elCambio.classList.add('insuficiente');
  } else {
    elCambio.textContent = formatCOP(diferencia);
    elCambio.classList.remove('insuficiente');
  }
}
 
/* ══ EMITIR FACTURA ═════════════════════════════════ */
async function emitirFactura() {
  if (!citaSeleccionada) { mostrarToast('⚠️ Selecciona una cita primero', 'warn'); return; }
 
  const idTipo      = parseInt(document.getElementById('tipo-tratamiento').value);
  const diagnostico = document.getElementById('diagnostico').value.trim();
  const precioBase  = parseFloat(document.getElementById('precio-base').value) || 0;
  const cobroExtra  = parseFloat(document.getElementById('cobro-extra').value) || 0;
  const idMetodo    = parseInt(document.querySelector('input[name="metodo"]:checked').value);
 
  const impuestoPorcentaje = document.getElementById('aplicar-iva').checked ? 19 : 0;
 
  /* Datos de efectivo */
  const esEfectivo    = idMetodo === 3;
  const montoRecibido = esEfectivo
    ? (parseFloat(document.getElementById('monto-recibido').value) || 0)
    : null;
  const valorIva   = (precioBase + cobroExtra) * (impuestoPorcentaje / 100);
  const totalFinal = precioBase + cobroExtra + valorIva;
  const cambio     = esEfectivo ? Math.max(0, montoRecibido - totalFinal) : null;
 
  /* Validaciones */
  if (!idTipo)      { mostrarToast('⚠️ Selecciona un tipo de tratamiento', 'warn'); return; }
  if (!diagnostico) { mostrarToast('⚠️ Escribe el diagnóstico', 'warn'); return; }
  if (esEfectivo && montoRecibido < totalFinal) {
    mostrarToast('⚠️ El monto recibido es menor al total a pagar', 'warn'); return;
  }
 
  const payload = {
    id_cita:        citaSeleccionada.id_cita,
    id_odontologo:  citaSeleccionada.id_odontologo,
    id_paciente:    citaSeleccionada.id_paciente,
    id_tipo:        idTipo,
    diagnostico,
    cobro_extra:    cobroExtra,
    id_metodo_pago: idMetodo,
    impuesto:       impuestoPorcentaje
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
    
    facturaActual = {
      id_factura:     data.id_factura,
      paciente:       citaSeleccionada.nombre_paciente,
      odontologo:     citaSeleccionada.nombre_odontologo,
      sala:           citaSeleccionada.nombre_sala,
      fecha_cita:     citaSeleccionada.fecha,
      tratamiento:    nombreTratamiento,
      diagnostico,
      precio_base:    precioBase,
      cobro_extra:    cobroExtra,
      iva:            valorIva,
      total:          totalFinal,
      metodo:         ['', 'Tarjeta débito/crédito', 'Transferencia bancaria', 'Efectivo'][idMetodo],
      monto_recibido: montoRecibido,
      cambio:         cambio,
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
  const pBase      = f.precio_base    !== undefined ? f.precio_base    : (f.precioBase || 0);
  const cExtra     = f.cobro_extra    !== undefined ? f.cobro_extra    : (f.cobroExtra || 0);
  const ivaFactura = f.iva            !== undefined ? f.iva            : (f.valorIva   || 0);
  const recibido   = f.monto_recibido !== undefined ? f.monto_recibido : null;
  const cambio     = f.cambio         !== undefined ? f.cambio         : null;

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
      <thead>
        <tr>
          <th>Tratamiento</th>
          <th>Diagnóstico</th>
          <th>Precio base</th>
          <th>Cobro extra</th>
          <th>IVA (19%)</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>${f.tratamiento}</td>
          <td>${f.diagnostico || '—'}</td>
          <td>${formatCOP(pBase)}</td>
          <td>${formatCOP(cExtra)}</td>
          <td>${formatCOP(ivaFactura)}</td>
          <td>${formatCOP(f.total)}</td>
        </tr>
      </tbody>
    </table>
    <div class="factura-total">TOTAL PAGADO: ${formatCOP(f.total)}</div>
    ${recibido != null ? `
    <div style="margin-top:12px; padding:14px 18px; background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.25); border-radius:12px; display:flex; flex-direction:column; gap:8px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:13px; color:#10b981; font-weight:600;">💵 Monto recibido</span>
        <span style="font-size:15px; color:#10b981; font-weight:700;">${formatCOP(recibido)}</span>
      </div>
      <div style="border-top:1px solid rgba(16,185,129,.2); padding-top:8px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:13px; color:#10b981; font-weight:600;">💰 Cambio a devolver</span>
        <span style="font-size:18px; color:#10b981; font-weight:800;">${formatCOP(cambio)}</span>
      </div>
    </div>` : ''}
  `;
  document.getElementById('modal-factura').classList.add('visible');
}
 
function cerrarModal() {
  document.getElementById('modal-factura').classList.remove('visible');
}
 
/* ══ HISTORIAL DE PAGOS ═════════════════════════════ */
function verPagos() {
  let html = `<h2 style="margin-bottom:4px">📂 Historial de facturas</h2>`;
  html += `<p style="font-size: 12px; color: var(--muted); margin-bottom: 14px;">💡 Haz clic en cualquier fila para ver el desglose completo de la factura.</p>`;
 
  if (pagosLocales.length === 0) {
    html += `<p style="color:var(--muted)">No hay facturas registradas en esta sesión.</p>`;
  } else {
    html += `<table class="tabla-pagos">
      <thead>
        <tr>
          <th>#</th>
          <th>Paciente</th>
          <th>Tratamiento</th>
          <th>Total</th>
          <th>Método</th>
          <th>Cambio</th>
        </tr>
      </thead>
      <tbody>`;
    pagosLocales.forEach(p => {
      const filaEfectivo = p.cambio != null
        ? `<td style="color:#15803d; font-weight:600;">💵 ${formatCOP(p.cambio)}</td>`
        : `<td style="color:var(--muted);">—</td>`;
      html += `
      <tr onclick="verFacturaHistorica(${p.id_factura})" style="cursor: pointer;" title="Haga clic para expandir factura">
        <td><strong>#${p.id_factura}</strong></td>
        <td>${p.paciente}</td>
        <td>${p.tratamiento}</td>
        <td>${formatCOP(p.total)}</td>
        <td>${p.metodo || '—'}</td>
        ${filaEfectivo}
      </tr>`;
    });
    html += `</tbody></table>`;
  }
 
  document.getElementById('contenido-pagos').innerHTML = html;
  
  const modalPagos = document.getElementById('modal-pagos');
  modalPagos.style.display = 'flex';
  modalPagos.classList.add('visible');
}
 
/* ══ MÉTODOS DE PAGO – UI ═══════════════════════════ */
function inicializarMetodosPago() {
  document.querySelectorAll('.metodo-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('.metodo-card').forEach(c => c.classList.remove('activo'));
      card.classList.add('activo');
      card.querySelector('input').checked = true;
 
      /* Mostrar u ocultar sección de efectivo */
      const esEfectivo = card.querySelector('input').value === '3';
      const seccion    = document.getElementById('seccion-efectivo');
      seccion.style.display = esEfectivo ? 'block' : 'none';
 
      if (!esEfectivo) {
        document.getElementById('monto-recibido').value  = '';
        document.getElementById('valor-cambio').textContent = formatCOP(0);
        document.getElementById('valor-cambio').style.color = '#15803d';
      }
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
 
function verFacturaHistorica(idFactura) {
  const facturaEnc = pagosLocales.find(p => p.id_factura === idFactura);
  if (facturaEnc) {
    const modalPagos = document.getElementById('modal-pagos');
    modalPagos.classList.remove('visible');
    modalPagos.style.display = 'none';
    mostrarFacturaModal(facturaEnc);
  }
}
 