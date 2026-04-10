/* =====================
   DATOS INICIALES
===================== */
let pacientes = JSON.parse(localStorage.getItem("pacientes")) || [
  { nombre: "Juan Pérez",    documento: "87654321" },
  { nombre: "María López",   documento: "12345678" },
  { nombre: "Carlos Torres", documento: "99887766" }
];

let tratamientos       = [];
let consultaActiva     = false;
let totalFinal         = 0;
let facturaGenerada    = false;
let pacienteAsistio    = true; // por defecto: sí asistió

let pagos              = JSON.parse(localStorage.getItem("pagos"))              || [];
let facturasEliminadas = JSON.parse(localStorage.getItem("facturasEliminadas")) || [];
let inasistencias      = JSON.parse(localStorage.getItem("inasistencias"))      || [];
let numeroFactura      = parseInt(localStorage.getItem("numeroFactura"))        || 1;

/* =====================
   BASE DE TRATAMIENTOS
===================== */
const tratamientosDB = {
  "Dra. Paula Ríos - Ortodoncia": [
    { nombre: "Consulta Ortodoncia",   precio: 75  },
    { nombre: "Brackets Metálicos",    precio: 300 },
    { nombre: "Brackets Estéticos",    precio: 450 },
    { nombre: "Retenedor",             precio: 120 },
    { nombre: "Control Mensual",       precio: 40  }
  ],
  "Dr. Carlos Méndez - Endodoncia": [
    { nombre: "Endodoncia Unirradicular",   precio: 200 },
    { nombre: "Endodoncia Multirradicular", precio: 350 },
    { nombre: "Retratamiento",             precio: 280 },
    { nombre: "Radiografía",               precio: 30  }
  ],
  "Dra. Laura Sánchez - Odontología General": [
    { nombre: "Consulta General",  precio: 50  },
    { nombre: "Limpieza Dental",   precio: 60  },
    { nombre: "Resina Dental",     precio: 90  },
    { nombre: "Extracción Simple", precio: 110 },
    { nombre: "Blanqueamiento",    precio: 250 }
  ]
};

/* =====================
   PACIENTES
===================== */
function cargarPacientes() {
  let select = document.getElementById("selectPaciente");
  select.innerHTML = '<option value="">Seleccione</option>';
  pacientes.forEach((p, i) => {
    select.innerHTML += `<option value="${i}">${p.nombre}</option>`;
  });
}

function seleccionarPaciente() {
  let index = document.getElementById("selectPaciente").value;
  if (index === "") return;
  let p = pacientes[index];
  document.getElementById("nombre").value    = p.nombre;
  document.getElementById("documento").value = p.documento;
}

function crearPaciente() {
  let nom = document.getElementById("nombre").value.trim();
  let doc = document.getElementById("documento").value.trim();

  if (nom === "" || doc === "") { alert("Ingrese nombre y documento"); return; }
  if (pacientes.some(p => p.documento === doc)) { alert("Paciente ya registrado"); return; }

  pacientes.push({ nombre: nom, documento: doc });
  localStorage.setItem("pacientes", JSON.stringify(pacientes));
  cargarPacientes();
  alert("Paciente agregado");
}

function eliminarPaciente() {
  let index = document.getElementById("selectPaciente").value;
  if (index === "") { alert("Seleccione un paciente"); return; }
  if (!confirm("¿Seguro que desea eliminar este paciente?")) return;

  pacientes.splice(index, 1);
  cargarPacientes();
  document.getElementById("nombre").value    = "";
  document.getElementById("documento").value = "";
  document.getElementById("selectPaciente").value = "";
  alert("Paciente eliminado");
}

function historialPaciente() {
  let doc = document.getElementById("documento").value;
  if (doc === "") { alert("Seleccione un paciente"); return; }

  let nombrePaciente   = document.getElementById("nombre").value;
  let facturasPaciente = pagos.filter(p => p.paciente === nombrePaciente);

  let contenido = `<h2>Historial de ${nombrePaciente}</h2>
  <table class="table">
    <tr><th>Factura</th><th>Total</th><th>Acción</th></tr>`;

  facturasPaciente.forEach(f => {
    contenido += `
    <tr>
      <td>${f.factura}</td>
      <td>$${f.total.toFixed(2)}</td>
      <td><button onclick="verDetalleFactura(${pagos.indexOf(f)})" class="btn-primary">Ver</button></td>
    </tr>`;
  });

  contenido += `</table><br>
  <button onclick="cerrarPagos()" class="btn-primary">Cerrar</button>`;

  document.getElementById("contenidoPagos").innerHTML = contenido;
  document.getElementById("modalPagos").style.display = "flex";
}

/* =====================
   CONSULTA
===================== */
function crearConsulta() {
  if (document.getElementById("nombre").value === "" || document.getElementById("documento").value === "") {
    alert("Seleccione paciente");
    return;
  }
  consultaActiva  = true;
  pacienteAsistio = true; // reset: por defecto sí asistió

  document.getElementById("consultaOK").style.display      = "block";
  document.getElementById("bloqueAsistencia").style.display = "block";

  // Resetear botones de asistencia
  document.getElementById("btnSi").classList.add("activo");
  document.getElementById("btnNo").classList.remove("activo");
  document.getElementById("motivoInasistenciaBox").style.display = "none";
  document.getElementById("motivoInasistencia").value = "";
}

function nuevaConsulta() {
  consultaActiva  = false;
  facturaGenerada = false;
  pacienteAsistio = true;
  tratamientos    = [];

  renderTabla();
  document.getElementById("consultaOK").style.display        = "none";
  document.getElementById("bloqueAsistencia").style.display  = "none";
  document.getElementById("diagnostico").value               = "";
  document.getElementById("motivoInasistencia").value        = "";
  document.getElementById("motivoInasistenciaBox").style.display = "none";

  // Resetear botones de asistencia
  document.getElementById("btnSi").classList.add("activo");
  document.getElementById("btnNo").classList.remove("activo");
}

/* =====================
   ASISTENCIA
===================== */
function setAsistencia(asistio) {
  pacienteAsistio = asistio;

  if (asistio) {
    document.getElementById("btnSi").classList.add("activo");
    document.getElementById("btnNo").classList.remove("activo");
    document.getElementById("motivoInasistenciaBox").style.display = "none";
    document.getElementById("btnGuardarInasistencia").style.display = "none"; // ← ocultar
  } else {
    document.getElementById("btnNo").classList.add("activo");
    document.getElementById("btnSi").classList.remove("activo");
    document.getElementById("motivoInasistenciaBox").style.display = "block";
    document.getElementById("btnGuardarInasistencia").style.display = "inline-block"; // ← mostrar
  }
}

function guardarInasistenciaDirecta() {
  if (!consultaActiva) { alert("Primero cree una consulta"); return; }

  let nombrePaciente = document.getElementById("nombre").value;
  if (!nombrePaciente) { alert("Seleccione un paciente"); return; }

  if (!confirm(`¿Registrar inasistencia de ${nombrePaciente}?`)) return;

  registrarInasistencia(); // usa tu función existente

  alert("✅ Inasistencia guardada correctamente.");

  // Limpiar consulta y paciente
  nuevaConsulta();
  document.getElementById("nombre").value = "";
  document.getElementById("documento").value = "";
  document.getElementById("selectPaciente").value = "";
  document.getElementById("btnGuardarInasistencia").style.display = "none";
}

function registrarInasistencia() {
  let motivo = document.getElementById("motivoInasistencia").value.trim() || "Sin motivo indicado";
  let doctor = document.getElementById("doctor").value;

  inasistencias.push({
    paciente:  document.getElementById("nombre").value,
    documento: document.getElementById("documento").value,
    doctor:    doctor,
    motivo:    motivo,
    fecha:     new Date().toLocaleString()
  });

  localStorage.setItem("inasistencias", JSON.stringify(inasistencias));
}

function verInasistencias() {
  let contenido = `<h2>⚠ Historial de Inasistencias</h2>`;

  if (inasistencias.length === 0) {
    contenido += `<p style="margin-top:15px; color:#64748b;">No hay inasistencias registradas.</p>`;
  } else {
    contenido += `
    <table class="table">
      <thead>
        <tr>
          <th>Paciente</th>
          <th>Documento</th>
          <th>Odontólogo</th>
          <th>Motivo</th>
          <th>Fecha</th>
          <th></th>
        </tr>
      </thead>
      <tbody>`;

    inasistencias.forEach((item, index) => {
      contenido += `
      <tr>
        <td>${item.paciente}</td>
        <td>${item.documento}</td>
        <td>${item.doctor}</td>
        <td>${item.motivo}</td>
        <td>${item.fecha}</td>
        <td>
          <button onclick="eliminarInasistencia(${index})" class="btn-danger"
            style="margin:0; padding:5px 10px;">Eliminar</button>
        </td>
      </tr>`;
    });

    contenido += `</tbody></table>`;
  }

  contenido += `<br><button onclick="cerrarInasistencias()" class="btn-primary">Cerrar</button>`;

  document.getElementById("contenidoInasistencias").innerHTML = contenido;
  document.getElementById("modalInasistencias").style.display = "flex";
}

function eliminarInasistencia(index) {
  if (!confirm("¿Eliminar este registro de inasistencia?")) return;
  inasistencias.splice(index, 1);
  localStorage.setItem("inasistencias", JSON.stringify(inasistencias));
  verInasistencias(); // refrescar modal
}

function cerrarInasistencias() {
  document.getElementById("modalInasistencias").style.display = "none";
}

/* =====================
   TRATAMIENTOS
===================== */
function actualizarTratamientos() {
  let doctor = document.getElementById("doctor").value;
  let lista  = document.getElementById("listaTratamientos");
  lista.innerHTML = "";
  tratamientosDB[doctor].forEach(t => {
    lista.innerHTML += `<option value="${t.precio}">${t.nombre}</option>`;
  });
}

function agregarTratamiento() {
  if (!consultaActiva) { alert("Primero cree una consulta"); return; }

  let lista  = document.getElementById("listaTratamientos");
  let nombre = lista.options[lista.selectedIndex].text;
  let precio = parseFloat(lista.value);

  tratamientos.push({ nombre, precio, cantidad: 1 });
  renderTabla();
  calcularTotal();
}

function renderTabla() {
  let tabla = document.getElementById("tabla");
  tabla.innerHTML = "";

  tratamientos.forEach((t, i) => {
    let subtotal = t.precio * t.cantidad;
    tabla.innerHTML += `
    <tr>
      <td>${t.nombre}</td>
      <td>$${t.precio.toFixed(2)}</td>
      <td><input type="number" value="${t.cantidad}" min="1"
            onchange="cambiarCantidad(${i}, this.value)"></td>
      <td>$${subtotal.toFixed(2)}</td>
      <td><button onclick="eliminar(${i})">X</button></td>
    </tr>`;
  });

  calcularTotal();
}

function cambiarCantidad(i, val) {
  let cantidad = parseInt(val);
  if (isNaN(cantidad) || cantidad < 1) cantidad = 1;
  tratamientos[i].cantidad = cantidad;
  renderTabla();
}

function eliminar(i) {
  tratamientos.splice(i, 1);
  renderTabla();
}

/* =====================
   CÁLCULO DE TOTALES
===================== */
function calcularTotal() {
  let subtotalCalc = 0;
  tratamientos.forEach(t => { subtotalCalc += t.precio * t.cantidad; });

  let descuentoPorc = Math.min(Math.max(parseFloat(document.getElementById("descuento").value) || 0, 0), 100);
  let impuestoPorc  = Math.min(Math.max(parseFloat(document.getElementById("impuesto").value)  || 0, 0), 100);

  let descuento = subtotalCalc * (descuentoPorc / 100);
  let base      = subtotalCalc - descuento;
  let impuesto  = base * (impuestoPorc / 100);

  totalFinal = base + impuesto;

  document.getElementById("subtotal").innerText = "$" + subtotalCalc.toFixed(2);
  document.getElementById("total").innerText    = totalFinal.toFixed(2);
}

/* =====================
   FACTURA
===================== */
function emitirFactura() {
  if (!consultaActiva)        { alert("Primero cree una consulta"); return; }
  if (tratamientos.length === 0) { alert("No hay tratamientos");       return; }

  // Si el paciente no asistió, registrar inasistencia y no emitir factura
  if (!pacienteAsistio) {
    if (!confirm("El paciente no asistió. ¿Registrar la inasistencia y cerrar la consulta?")) return;
    registrarInasistencia();
    alert("Inasistencia registrada correctamente.");
    nuevaConsulta();
    document.getElementById("nombre").value    = "";
    document.getElementById("documento").value = "";
    document.getElementById("selectPaciente").value = "";
    return;
  }

  let tablaTratamientos = "";
  tratamientos.forEach(t => {
    let sub = t.precio * t.cantidad;
    tablaTratamientos += `
    <tr>
      <td>${t.nombre}</td><td>${t.cantidad}</td>
      <td>$${t.precio.toFixed(2)}</td><td>$${sub.toFixed(2)}</td>
    </tr>`;
  });

  let doctorSeleccionado = document.getElementById("doctor").value;
  let nombrePaciente     = document.getElementById("nombre").value;
  let docPaciente        = document.getElementById("documento").value;

  let cuerpoFactura = `
    <div class="factura-header">
      <h2>CLINIDENT</h2>
      <p>Factura #${numeroFactura}</p>
    </div>
    <p><strong>Paciente:</strong> ${nombrePaciente}</p>
    <p><strong>Documento:</strong> ${docPaciente}</p>
    <p><strong>Odontólogo:</strong> ${doctorSeleccionado}</p>
    <hr>
    <table class="table">
      <tr><th>Tratamiento</th><th>Cant</th><th>Precio</th><th>Subtotal</th></tr>
      ${tablaTratamientos}
    </table>
    <h2>Total: $${totalFinal.toFixed(2)}</h2>
  `;

  document.getElementById("contenidoFactura").innerHTML = cuerpoFactura + `
    <div class="no-print" style="margin-top:20px;">
      <button onclick="registrarPago()" class="btn-success">Confirmar y Pagar</button>
      <button onclick="cerrarFactura()"  class="btn-primary">Cerrar</button>
    </div>
  `;

  document.getElementById("modalFactura").style.display = "flex";
  facturaGenerada = true;
}

function cerrarFactura() {
  document.getElementById("modalFactura").style.display = "none";
}

function registrarPago() {
  if (!facturaGenerada)                          { alert("Primero emita factura"); return; }
  if (pagos.some(p => p.factura === numeroFactura)) { alert("Factura ya pagada");   return; }

  let tempDiv = document.createElement("div");
  tempDiv.innerHTML = document.getElementById("contenidoFactura").innerHTML;
  let botones = tempDiv.querySelector(".no-print");
  if (botones) botones.remove();

  pagos.push({
    factura:     numeroFactura,
    paciente:    document.getElementById("nombre").value,
    total:       totalFinal,
    detalleHTML: tempDiv.innerHTML
  });

  localStorage.setItem("pagos", JSON.stringify(pagos));
  alert("Pago registrado con éxito");

  numeroFactura++;
  localStorage.setItem("numeroFactura", numeroFactura);

  nuevaConsulta();
  document.getElementById("nombre").value    = "";
  document.getElementById("documento").value = "";
  document.getElementById("selectPaciente").value = "";

  cerrarFactura();
}

/* =====================
   PAGOS / HISTORIAL
===================== */
function verPagos() {
  let contenido = `<h2>Historial de Pagos</h2>
  <table class="table">
    <tr><th>Factura</th><th>Paciente</th><th>Total</th><th>Acciones</th></tr>`;

  pagos.forEach((p, index) => {
    contenido += `
    <tr>
      <td>${p.factura}</td>
      <td>${p.paciente}</td>
      <td>$${p.total.toFixed(2)}</td>
      <td>
        <button onclick="verDetalleFactura(${index})" class="btn-primary" style="margin:0;padding:5px 10px;">Ver</button>
        <button onclick="eliminarFactura(${index})"   class="btn-danger"  style="margin:0;padding:5px 10px;">Eliminar</button>
      </td>
    </tr>`;
  });

  contenido += `</table><br>
  <button onclick="cerrarPagos()" class="btn-primary">Cerrar</button>`;

  document.getElementById("contenidoPagos").innerHTML = contenido;
  document.getElementById("modalPagos").style.display = "flex";
}

function verDetalleFactura(index) {
  let pago = pagos[index];
  if (pago && pago.detalleHTML) {
    document.getElementById("contenidoFactura").innerHTML = pago.detalleHTML + `
      <div style="margin-top:20px;">
        <button onclick="window.print()" class="btn-success">Imprimir PDF</button>
        <button onclick="cerrarFactura()"  class="btn-primary">Regresar</button>
      </div>`;

    document.getElementById("modalPagos").style.display   = "none";
    document.getElementById("modalFactura").style.display = "flex";
  }
}

function eliminarFactura(index) {
  let motivo = prompt("Ingrese el motivo de eliminación de la factura:");
  if (!motivo || motivo.trim() === "") { alert("Debe ingresar un motivo"); return; }

  let factura = pagos[index];
  facturasEliminadas.push({
    factura:  factura.factura,
    paciente: factura.paciente,
    total:    factura.total,
    motivo:   motivo,
    fecha:    new Date().toLocaleString()
  });

  localStorage.setItem("facturasEliminadas", JSON.stringify(facturasEliminadas));
  pagos.splice(index, 1);
  localStorage.setItem("pagos", JSON.stringify(pagos));
  alert("Factura eliminada y registrada");
  verPagos();
}

function cerrarPagos() {
  document.getElementById("modalPagos").style.display = "none";
}

/* =====================
   INICIALIZACIÓN
===================== */
actualizarTratamientos();
cargarPacientes();