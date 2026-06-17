/**
 * CLINIDENT - Sistema de Agenda Interactiva (Módulo Paciente)
 * Archivo: agenda_cliente.js
 */
 
const API_URL = "/agenda_cliente/agenda_cliente";
let ID_USUARIO_LOGUEADO = null;
 
const TRATAMIENTOS = [
    { id: "limpieza",    nombre: "Limpieza Dental",   desc: "Profilaxis profunda y eliminación de sarro bacteriano.",          duracion: "45 MIN",  doctor: "Dr. Alberto Casas (General)",       icono: "🦷" },
    { id: "revision",    nombre: "Revisión General",  desc: "Evaluación integral de salud oral y diagnóstico.",               duracion: "30 MIN",  doctor: "Dr. Alberto Casas (General)",       icono: "🩺" },
    { id: "ortodoncia",  nombre: "Ortodoncia",         desc: "Ajuste y control de aparatología o brackets.",                   duracion: "60 MIN",  doctor: "Dra. Elena Marín (Ortodoncia)",     icono: "😁" },
    { id: "endodoncia",  nombre: "Endodoncia",         desc: "Tratamiento de conductos radiculares y alivio del dolor.",       duracion: "90 MIN",  doctor: "Dr. Camilo Ruiz (Cirugía)",         icono: "💉" },
    { id: "cirugia",     nombre: "Cirugía Oral",       desc: "Extracciones complejas y procedimientos quirúrgicos.",           duracion: "120 MIN", doctor: "Dr. Camilo Ruiz (Cirugía)",         icono: "🔬" }
];
 
const HORARIOS_MAESTROS = [
    "08:00 AM", "08:45 AM", "09:30 AM", "10:15 AM", "11:00 AM", "11:45 AM",
    "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM"
];
 
let tratamientoSeleccionado = null;
 
// =========================================================================
// ─── INICIALIZACIÓN
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    fetch(`${API_URL}?action=get_sesion_usuario`)
        .then(res => res.json())
        .then(user => {
            if (user.status === "success") {
                ID_USUARIO_LOGUEADO = user.id;
                document.getElementById("nav-user-display").innerText   = user.nombre;
                document.getElementById("nombre-usuario-bienvenida").innerText = user.nombre;
 
                // ── BOTONES DE NAVEGACIÓN A PANELES ──────────────────────
                // Se genera un botón por cada panel al que el usuario tiene acceso.
                // El botón "Vista Paciente" ya está aquí (es esta misma página).
                const roles = user.roles || [user.id_rol];
                const navBadge = document.querySelector(".user-badge");

                // Eliminar botones de panel previos (por si se recarga)
                navBadge.querySelectorAll(".btn-panel-dinamico").forEach(b => b.remove());

                // Botón panel médico (Aparece si es Odontólogo (2) o Administrador (1))
                if (roles.includes(2) || roles.includes(1)) {
                    const btn = document.createElement("button");
                    btn.className   = "btn-switch-module btn-panel-dinamico";
                    btn.innerText   = "🩺 Panel Médico";
                    btn.onclick     = () => window.location.href = '../odontologo/panel_medico.html';
                    // Insertar antes del botón Salir
                    navBadge.insertBefore(btn, document.querySelector(".btn-logout"));
                }

                // Botón panel recepción (Aparece si es Recepcionista (3) o Administrador (1))
                if (roles.includes(3) || roles.includes(1)) {
                    const btn = document.createElement("button");
                    btn.className   = "btn-switch-module btn-panel-dinamico";
                    btn.style.background = "#0ea5e9";
                    btn.style.color      = "white";
                    btn.innerText   = "📋 Panel Recepción";
                    btn.onclick     = () => window.location.href = '../recepcionista/panel_rec.html';
                    navBadge.insertBefore(btn, document.querySelector(".btn-logout"));
                }

                // Ocultar el btn-volver-mi-panel estático (ya no se usa)
                const btnVolverViejo = document.getElementById("btn-volver-mi-panel");
                if (btnVolverViejo) btnVolverViejo.style.display = "none";
 
                cargarOdontologos();
            }
        })
        .catch(err => console.error("Error al obtener sesión:", err));
 
    const inputFecha = document.getElementById("fecha");
    if (inputFecha) inputFecha.min = new Date().toISOString().split('T')[0];
 
    cambiarVista('menu');
});
 
function cambiarVista(vistaId) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const dest = document.getElementById(`view-${vistaId}`);
    if (dest) dest.classList.add('active');
}
 
// =========================================================================
// ─── FLUJO: TRATAMIENTOS
// =========================================================================
function cargarOdontologos() {
    fetch(`${API_URL}?action=get_odontologos`)
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                const selectDoc = document.getElementById("doc");
                if (!selectDoc) return;
                selectDoc.innerHTML = '<option value="">Seleccione un especialista</option>';
                response.data.forEach(doc => {
                    if (doc.id == ID_USUARIO_LOGUEADO) return; // anti-autoconsulta
                    const option = document.createElement("option");
                    option.value = doc.id;
                    option.text  = doc.nombre;
                    selectDoc.appendChild(option);
                });
                if (selectDoc.options.length <= 1)
                    selectDoc.innerHTML = '<option value="">No hay otros especialistas disponibles</option>';
            }
        })
        .catch(err => console.error("Error al cargar odontólogos:", err));
}
 
function abrirSelectorTratamiento() {
    document.getElementById("edit-id").value = "";
    document.getElementById("titulo-agendar").innerText = "Planifica tu visita";
    tratamientoSeleccionado = null;
 
    const grid = document.getElementById("grid-tratamientos");
    grid.innerHTML = "";
    TRATAMIENTOS.forEach(t => {
        const card = document.createElement("div");
        card.className = "tratamiento-card";
        card.id        = `tcard-${t.id}`;
        card.onclick   = () => seleccionarTratamientoCard(t);
        card.innerHTML = `
            <div class="tcard-icon">${t.icono}</div>
            <div class="tcard-info">
                <div class="tcard-nombre">${t.nombre}</div>
                <div class="tcard-desc">${t.desc}</div>
                <div class="tcard-duracion">⏱ ${t.duracion}</div>
            </div>
            <div class="tcard-check" id="check-${t.id}">✓</div>
        `;
        grid.appendChild(card);
    });
 
    document.getElementById("btn-continuar-trat").disabled = true;
    document.getElementById("btn-continuar-trat").classList.remove("ready");
    cambiarVista('tratamiento');
}
 
function seleccionarTratamientoCard(tratamiento) {
    tratamientoSeleccionado = tratamiento;
    document.querySelectorAll('.tratamiento-card').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.tcard-check').forEach(ch => ch.classList.remove('visible'));
    document.getElementById(`tcard-${tratamiento.id}`).classList.add('selected');
    document.getElementById(`check-${tratamiento.id}`).classList.add('visible');
    const btn = document.getElementById("btn-continuar-trat");
    btn.disabled = false;
    btn.classList.add("ready");
}
 
function confirmarTratamiento() {
    if (!tratamientoSeleccionado) return;
    document.getElementById("trat-icon-header").innerText   = tratamientoSeleccionado.icono;
    document.getElementById("trat-nombre-header").innerText = tratamientoSeleccionado.nombre;
    document.getElementById("trat-duracion-header").innerText = tratamientoSeleccionado.duracion;
    document.getElementById("trat-doctor-header").innerText = tratamientoSeleccionado.doctor;
 
    const selectDoc = document.getElementById("doc");
    selectDoc.selectedIndex = 0;
    for (let i = 0; i < selectDoc.options.length; i++) {
        let texto = selectDoc.options[i].text.toLowerCase().replace("dr. ","").replace("dra. ","").trim();
        if (texto !== "" && tratamientoSeleccionado.doctor.toLowerCase().includes(texto)) {
            selectDoc.selectedIndex = i; break;
        }
    }
 
    const inputFecha = document.getElementById("fecha");
    if (!inputFecha.value) inputFecha.value = new Date().toISOString().split('T')[0];
    document.getElementById("hora-seleccionada").value = "";
    actualizarAgenda();
    cambiarVista('agendar');
}
 
function volverATratamiento() { cambiarVista('tratamiento'); }
 
// =========================================================================
// ─── FLUJO: DISPONIBILIDAD HORARIA
// =========================================================================
function actualizarAgenda() {
    const fecha    = document.getElementById("fecha").value;
    const doctorId = document.getElementById("doc").value;
    const editId   = document.getElementById("edit-id").value;
    if (!fecha || !doctorId) return;
 
    let url = `${API_URL}?action=get_citas_ocupadas&fecha=${fecha}&doctor=${encodeURIComponent(doctorId)}`;
    if (editId) url += `&edit_id=${editId}`;
 
    fetch(url)
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") renderSlotsHorarios(response.data);
            else mostrarToast("Error al mapear franjas horarias.");
        })
        .catch(err => console.error(err));
}
 
function renderSlotsHorarios(horasOcupadas) {
    const gridHoras = document.getElementById("grid-horas");
    gridHoras.innerHTML = "";
    const horaPrevia = document.getElementById("hora-seleccionada").value;
    HORARIOS_MAESTROS.forEach(hora => {
        const slot = document.createElement("div");
        slot.className = "hora-slot";
        slot.innerText = hora;
        if (horasOcupadas.includes(hora)) {
            slot.classList.add("occupied");
        } else {
            if (hora === horaPrevia) slot.classList.add("selected");
            slot.onclick = () => seleccionarHoraSlot(slot, hora);
        }
        gridHoras.appendChild(slot);
    });
}
 
function seleccionarHoraSlot(elemento, hora) {
    document.querySelectorAll('.hora-slot').forEach(s => s.classList.remove('selected'));
    elemento.classList.add('selected');
    document.getElementById("hora-seleccionada").value = hora;
}
 
// =========================================================================
// ─── OPERACIONES POST
// =========================================================================
function finalizarAgendado() {
    const editId   = document.getElementById("edit-id").value;
    const fecha    = document.getElementById("fecha").value;
    const doctorId = document.getElementById("doc").value;
    const hora     = document.getElementById("hora-seleccionada").value;
 
    // Capturar nombre del doctor para el modal
    const docSelect   = document.getElementById("doc");
    const doctorNombre = docSelect.options[docSelect.selectedIndex]
                         ? docSelect.options[docSelect.selectedIndex].text
                         : "Especialista";
 
    if (!fecha || !hora || !doctorId) {
        mostrarToast("⚠️ Por favor selecciona fecha, horario y especialista."); return;
    }
 
    fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            edit_id:    editId || null,
            doctor_id:  doctorId,
            fecha, hora,
            tratamiento: tratamientoSeleccionado ? tratamientoSeleccionado.nombre : "Limpieza Dental"
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // === REGLA R4: CARGAR DETALLES EN EL MODAL DE NOTIFICACIÓN ===
            const nombreTratamiento = tratamientoSeleccionado
                ? tratamientoSeleccionado.nombre
                : "Tratamiento Odontológico";
 
            // Formatear fecha a DD/MM/YYYY para mostrar más legible
            const partesFecha = fecha.split("-");
            const fechaLegible = partesFecha.length === 3
                ? `${partesFecha[2]}/${partesFecha[1]}/${partesFecha[0]}`
                : fecha;
 
            document.getElementById("notif-tratamiento").innerText = nombreTratamiento;
            document.getElementById("notif-doctor").innerText      = doctorNombre;
            document.getElementById("notif-fecha").innerText       = fechaLegible;
            document.getElementById("notif-hora").innerText        = hora;
 
            // Mostrar el modal emergente detallado
            document.getElementById("modal-notificacion").style.display = "flex";
 
            // Refrescar lista en segundo plano
            renderLista();
        } else {
            mostrarToast("❌ " + data.message);
        }
    })
    .catch(err => console.error(err));
}
 
// ─── MODAL DE NOTIFICACIÓN: cerrar y volver al menú ───────────────────────
function cerrarModalNotificacion() {
    document.getElementById("modal-notificacion").style.display = "none";
    cambiarVista('menu');
}
 
// =========================================================================
// ─── HISTORIAL Y EDICIÓN
// =========================================================================
function renderLista() {
    const contenedor = document.getElementById("lista-citas");
    contenedor.innerHTML = '<div class="empty-msg">Consultando base de datos central...</div>';

    fetch(`${API_URL}?action=get_citas_usuario`)
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                contenedor.innerHTML = "";
                const citas = response.data;
                if (citas.length === 0) {
                    contenedor.innerHTML = '<div class="empty-msg">No registras citas médicas en el sistema.</div>';
                    return;
                }

                // ── Separar citas activas e historial ────────────────────
                const activas    = citas.filter(c => [1, 3].includes(c.id_estado));
                const historial  = citas.filter(c => ![1, 3].includes(c.id_estado));

                const renderGrupo = (lista, titulo) => {
                    if (lista.length === 0) return;

                    const encabezado = document.createElement("div");
                    encabezado.className = "historial-seccion-titulo";
                    encabezado.innerText = titulo;
                    contenedor.appendChild(encabezado);

                    lista.forEach(c => {
                        const fPartes = c.fecha.split("-");
                        const fechaLegible = fPartes.length === 3
                            ? `${fPartes[2]}/${fPartes[1]}/${fPartes[0]}`
                            : c.fecha;

                        const esActiva = [1, 3].includes(c.id_estado);

                        const item = document.createElement("div");
                        item.className = "report-item";
                        item.style.borderLeftColor = c.color_estado;

                        item.innerHTML = `
                            <div class="tcard-info">
                                <div class="tcard-nombre">${c.tratamientoIcono} ${c.tratamiento}</div>
                                <div class="tcard-desc" style="margin-top:4px;">
                                    Especialista: <strong>${c.doctor}</strong>
                                </div>
                                <div class="tcard-duracion" style="margin-top:4px; color:var(--text-primary);">
                                    📅 ${fechaLegible} &nbsp;|&nbsp; ⏱ ${c.hora}
                                </div>
                                <div style="margin-top:6px; font-size:0.8rem; font-weight:700;
                                            color:${c.color_estado}; text-transform:uppercase;
                                            letter-spacing:0.4px;">
                                    ${c.icono_estado} ${c.nombre_estado}
                                </div>
                            </div>
                            <div class="actions-btns">
                                ${esActiva ? `
                                    <button class="btn-edit"        onclick="iniciarEdicion(${c.id})">Reprogramar</button>
                                    <button class="btn-cancel-cita" onclick="eliminarCita(${c.id})">Cancelar</button>
                                ` : ''}
                            </div>
                        `;
                        contenedor.appendChild(item);
                    });
                };

                renderGrupo(activas,   "📅 Citas Activas");
                renderGrupo(historial, "🗂️ Historial");

            } else {
                contenedor.innerHTML = '<div class="empty-msg">Error al extraer el historial.</div>';
            }
        })
        .catch(err => console.error(err));
}
 
function iniciarEdicion(idCita) {
    fetch(`${API_URL}?action=get_una_cita&id_cita=${idCita}`)
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                const cita = response.data;
                document.getElementById("edit-id").value              = cita.id;
                document.getElementById("titulo-agendar").innerText   = "Modificar / Reprogramar Cita";
                document.getElementById("fecha").value                = cita.fecha;
                document.getElementById("hora-seleccionada").value    = cita.hora;
                tratamientoSeleccionado = TRATAMIENTOS.find(t => t.nombre === cita.tratamiento) || TRATAMIENTOS[0];
                document.getElementById("trat-icon-header").innerText   = cita.tratamientoIcono;
                document.getElementById("trat-nombre-header").innerText = cita.tratamiento;
                document.getElementById("trat-duracion-header").innerText = tratamientoSeleccionado.duracion;
                document.getElementById("trat-doctor-header").innerText = cita.doctor;
                actualizarAgenda();
                cambiarVista('agendar');
            }
        })
        .catch(err => console.error(err));
}
 
function eliminarCita(idCita) {
    document.getElementById("modal-cancelacion-id").value = idCita;
    document.getElementById("motivo-cancelacion-texto").value = "";
    document.getElementById("modal-cancelacion-error").style.display = "none";
    document.getElementById("modal-cancelacion").style.display = "flex";
}

function cerrarModalCancelacion() {
    document.getElementById("modal-cancelacion").style.display = "none";
}

function confirmarCancelacion() {
    const idCita = document.getElementById("modal-cancelacion-id").value;
    const motivo = document.getElementById("motivo-cancelacion-texto").value.trim();
    const errorEl = document.getElementById("modal-cancelacion-error");

    if (!motivo) {
        errorEl.style.display = "block";
        errorEl.innerText = "⚠️ Por favor escribe el motivo antes de continuar.";
        return;
    }
    if (motivo.length < 10) {
        errorEl.style.display = "block";
        errorEl.innerText = "⚠️ El motivo debe tener al menos 10 caracteres.";
        return;
    }

    errorEl.style.display = "none";

    fetch(`${API_URL}?action=cancelar_cita`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_cita: idCita, motivo_cancelacion: motivo })
    })
    .then(res => res.json())
    .then(data => {
        cerrarModalCancelacion();
        if (data.status === "success") {
            mostrarToast("✅ Cita cancelada correctamente.");
            renderLista();
        } else {
            mostrarToast("❌ " + data.message);
        }
    })
    .catch(err => console.error(err));
}
 
function mostrarToast(mensaje) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = mensaje;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
}
 
function cerrarSesion() {
    if (!confirm("¿Estás seguro de que deseas cerrar tu sesión actual?")) return;
    fetch('/logout', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
        .then(res => res.json())
        .then(data => { window.location.href = '/web/login/login.html'; })
        .catch(() => { window.location.href = '/web/login/login.html'; });
}
 
function irAModoMedico() {
    window.location.href = '../odontologo/panel_medico.html';
}
 