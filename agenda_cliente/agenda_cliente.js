
/**
 * CLINIDENT - Sistema de Agenda Interactiva (Módulo Paciente)
 * Archivo: agenda_cliente.js
 *
 * CAMBIO IMPORTANTE (rotación real de especialistas):
 * Ya no se fija un doctor de antemano. El frontend muestra las horas
 * disponibles considerando a TODOS los odontólogos del servicio (una
 * hora se bloquea solo si TODOS están ocupados), y el backend decide
 * qué doctor específico queda asignado en el momento de confirmar,
 * eligiendo entre los libres a esa hora al que tenga menos carga ese día.
 */
 
const API_URL = "/agenda_cliente/agenda_cliente";
let ID_USUARIO_LOGUEADO = null;
 
const TRATAMIENTOS = [
    { id: "limpieza",   nombre: "Limpieza Dental",  desc: "Profilaxis profunda y eliminación de sarro bacteriano.",        duracion: "45 MIN",  icono: "🦷", precio: 80000  },
    { id: "revision",   nombre: "Revisión General",  desc: "Evaluación integral de salud oral y diagnóstico.",             duracion: "30 MIN",  icono: "🩺", precio: 15000  },
    { id: "ortodoncia", nombre: "Ortodoncia",         desc: "Ajuste y control de aparatología o brackets.",                duracion: "60 MIN",  icono: "😁", precio: 150000 },
    { id: "endodoncia", nombre: "Endodoncia",         desc: "Tratamiento de conductos radiculares y alivio del dolor.",    duracion: "90 MIN",  icono: "💉", precio: 350000 },
    { id: "cirugia",    nombre: "Cirugía Oral",       desc: "Extracciones complejas y procedimientos quirúrgicos.",        duracion: "120 MIN", icono: "🔬", precio: 450000 }
];
 
// Mapeo de nombre JS → nombre exacto en BD (para la búsqueda de especialistas)
const NOMBRE_BD = {
    "Limpieza Dental":  "Limpieza dental",
    "Revisión General": "Revisión general",
    "Ortodoncia":       "Ortodoncia",
    "Endodoncia":       "Endodoncia",
    "Cirugía Oral":     "Cirugía oral"
};
 
// Formatea un valor numérico como pesos colombianos (ej: 150000 → "$150.000")
function formatearPrecio(valor) {
    return "$" + Number(valor).toLocaleString("es-CO");
}
 
// Trae los precios reales desde tbltipotratamiento y actualiza el array TRATAMIENTOS.
function cargarPreciosTratamientos() {
    fetch(`${API_URL}?action=get_tratamientos`)
        .then(res => res.json())
        .then(response => {
            if (response.status !== "success") return;
            const precios = response.data;
            TRATAMIENTOS.forEach(t => {
                const match = Object.keys(precios).find(
                    nombreBD => nombreBD.toLowerCase() === t.nombre.toLowerCase()
                );
                if (match) t.precio = precios[match];
            });
        })
        .catch(err => console.error("Error al cargar precios de tratamientos:", err));
}
 
const HORARIOS_MAESTROS = [
    "08:00 AM", "08:45 AM", "09:30 AM", "10:15 AM", "11:00 AM", "11:45 AM",
    "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM"
];
 
let tratamientoSeleccionado  = null;
let candidatosEspecialistas  = [];   // Lista de TODOS los odontólogos que atienden el tratamiento actual
 
// =========================================================================
// ─── INICIALIZACIÓN
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    fetch(`${API_URL}?action=get_sesion_usuario`)
        .then(res => res.json())
        .then(user => {
            if (user.status === "success") {
                ID_USUARIO_LOGUEADO = user.id;
                document.getElementById("nav-user-display").innerText            = user.nombre;
                document.getElementById("nombre-usuario-bienvenida").innerText   = user.nombre;
 
                // ── Botones de panel según roles ──────────────────────────
                const roles    = user.roles || [user.id_rol];
                const navBadge = document.querySelector(".user-badge");
 
                navBadge.querySelectorAll(".btn-panel-dinamico").forEach(b => b.remove());
 
                if (roles.includes(2) || roles.includes(1)) {
                    const btn       = document.createElement("button");
                    btn.className   = "btn-switch-module btn-panel-dinamico";
                    btn.innerText   = "🩺 Panel Médico";
                    btn.onclick     = () => window.location.href = '../odontologo/panel_medico.html';
                    navBadge.insertBefore(btn, document.querySelector(".btn-logout"));
                }
 
                if (roles.includes(3) || roles.includes(1)) {
                    const btn             = document.createElement("button");
                    btn.className         = "btn-switch-module btn-panel-dinamico";
                    btn.style.background  = "#0ea5e9";
                    btn.style.color       = "white";
                    btn.innerText         = "📋 Panel Recepción";
                    btn.onclick           = () => window.location.href = '../recepcionista/panel_rec.html';
                    navBadge.insertBefore(btn, document.querySelector(".btn-logout"));
                }
 
                const btnVolverViejo = document.getElementById("btn-volver-mi-panel");
                if (btnVolverViejo) btnVolverViejo.style.display = "none";
 
                cargarPreciosTratamientos();
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
// ─── FLUJO: SELECCIÓN DE TRATAMIENTO
// =========================================================================
function abrirSelectorTratamiento() {
    document.getElementById("edit-id").value          = "";
    document.getElementById("titulo-agendar").innerText = "Planifica tu visita";
    tratamientoSeleccionado = null;
    candidatosEspecialistas = [];
 
    const grid = document.getElementById("grid-tratamientos");
    grid.innerHTML = "";
    TRATAMIENTOS.forEach(t => {
        const card      = document.createElement("div");
        card.className  = "tratamiento-card";
        card.id         = `tcard-${t.id}`;
        card.onclick    = () => seleccionarTratamientoCard(t);
        card.innerHTML  = `
            <div class="tcard-icon">${t.icono}</div>
            <div class="tcard-info">
                <div class="tcard-nombre">${t.nombre}</div>
                <div class="tcard-desc">${t.desc}</div>
                <div class="tcard-meta-row">
                    <span class="tcard-duracion">⏱ ${t.duracion}</span>
                    <span class="tcard-precio">${formatearPrecio(t.precio)}</span>
                </div>
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
    const btn     = document.getElementById("btn-continuar-trat");
    btn.disabled  = false;
    btn.classList.add("ready");
}
 
// =========================================================================
// ─── FLUJO: CANDIDATOS DE ESPECIALISTAS (sin fijar doctor de antemano)
// =========================================================================
 
/**
 * Consulta al backend TODOS los odontólogos que atienden el tratamiento.
 * Ya no elige uno fijo aquí: solo guarda la lista completa. El backend
 * decide el doctor específico al momento de confirmar la reserva, según
 * quién esté libre en la hora elegida y tenga menos carga ese día.
 */
function cargarCandidatosTratamiento(nombreTratamiento) {
    const nombreBD = NOMBRE_BD[nombreTratamiento] || nombreTratamiento;
 
    return fetch(`${API_URL}?action=get_odontologos_por_tratamiento&tratamiento=${encodeURIComponent(nombreBD)}`)
        .then(res => res.json())
        .then(response => {
            if (response.status !== "success" || !response.data || response.data.length === 0) {
                mostrarToast("⚠️ No hay especialistas disponibles para este tratamiento.");
                candidatosEspecialistas = [];
                return [];
            }
            candidatosEspecialistas = response.data;
            return candidatosEspecialistas;
        });
}
 
function confirmarTratamiento() {
    if (!tratamientoSeleccionado) return;
 
    document.getElementById("trat-icon-header").innerText     = tratamientoSeleccionado.icono;
    document.getElementById("trat-nombre-header").innerText   = tratamientoSeleccionado.nombre;
    document.getElementById("trat-duracion-header").innerText = tratamientoSeleccionado.duracion;
    document.getElementById("trat-precio-header").innerText   = formatearPrecio(tratamientoSeleccionado.precio);
 
    cargarCandidatosTratamiento(tratamientoSeleccionado.nombre)
        .then(candidatos => {
            if (!candidatos.length) return;  // Toast ya mostrado en la función
 
            const inputFecha = document.getElementById("fecha");
            if (!inputFecha.value) inputFecha.value = new Date().toISOString().split("T")[0];
            document.getElementById("hora-seleccionada").value = "";
 
            actualizarAgenda();
            cambiarVista('agendar');
        })
        .catch(err => {
            console.error("Error al cargar especialistas:", err);
            mostrarToast("❌ Error al buscar especialistas. Intenta de nuevo.");
        });
}
 
function volverATratamiento() { cambiarVista('tratamiento'); }
 
// =========================================================================
// ─── FLUJO: DISPONIBILIDAD HORARIA (considerando TODOS los candidatos)
// =========================================================================
function actualizarAgenda() {
    const fecha  = document.getElementById("fecha").value;
    const editId = document.getElementById("edit-id").value;
    if (!fecha || !tratamientoSeleccionado) return;
 
    const nombreBD = NOMBRE_BD[tratamientoSeleccionado.nombre] || tratamientoSeleccionado.nombre;
 
    let url = `${API_URL}?action=get_citas_ocupadas&fecha=${fecha}&tratamiento=${encodeURIComponent(nombreBD)}`;
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
    const gridHoras  = document.getElementById("grid-horas");
    gridHoras.innerHTML = "";
    const horaPrevia = document.getElementById("hora-seleccionada").value;
 
    HORARIOS_MAESTROS.forEach(hora => {
        const slot      = document.createElement("div");
        slot.className  = "hora-slot";
        slot.innerText  = hora;
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
    const editId = document.getElementById("edit-id").value;
    const fecha  = document.getElementById("fecha").value;
    const hora   = document.getElementById("hora-seleccionada").value;
 
    if (!fecha || !hora) {
        mostrarToast("⚠️ Por favor selecciona fecha y un horario disponible.");
        return;
    }
 
    fetch(API_URL, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            edit_id:     editId || null,
            fecha,
            hora,
            tratamiento: tratamientoSeleccionado ? tratamientoSeleccionado.nombre : "Limpieza Dental"
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            const nombreTratamiento = tratamientoSeleccionado
                ? tratamientoSeleccionado.nombre
                : "Tratamiento Odontológico";
 
            const partesFecha  = fecha.split("-");
            const fechaLegible = partesFecha.length === 3
                ? `${partesFecha[2]}/${partesFecha[1]}/${partesFecha[0]}`
                : fecha;
 
            document.getElementById("notif-tratamiento").innerText = nombreTratamiento;
            document.getElementById("notif-doctor").innerText      = data.doctor_asignado || "Especialista";
            document.getElementById("notif-fecha").innerText       = fechaLegible;
            document.getElementById("notif-hora").innerText        = hora;
 
            document.getElementById("modal-notificacion").style.display = "flex";
            renderLista();  // refrescar en segundo plano
        } else {
            mostrarToast("❌ " + data.message);
        }
    })
    .catch(err => console.error(err));
}
 
function cerrarModalNotificacion() {
    document.getElementById("modal-notificacion").style.display = "none";
    cambiarVista('menu');
}
 
// =========================================================================
// ─── HISTORIAL Y EDICIÓN
// =========================================================================
function renderLista() {
    const contenedor    = document.getElementById("lista-citas");
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
 
                const activas   = citas.filter(c => [1, 3].includes(c.id_estado));
                const historial = citas.filter(c => ![1, 3].includes(c.id_estado));
 
                const renderGrupo = (lista, titulo) => {
                    if (lista.length === 0) return;
 
                    const encabezado      = document.createElement("div");
                    encabezado.className  = "historial-seccion-titulo";
                    encabezado.innerText  = titulo;
                    contenedor.appendChild(encabezado);
 
                    lista.forEach(c => {
                        const fPartes      = c.fecha.split("-");
                        const fechaLegible = fPartes.length === 3
                            ? `${fPartes[2]}/${fPartes[1]}/${fPartes[0]}`
                            : c.fecha;
 
                        const esActiva = [1, 3].includes(c.id_estado);
                        const tInfo    = TRATAMIENTOS.find(
                            t => t.nombre.toLowerCase() === c.tratamiento.toLowerCase()
                        );
 
                        const item      = document.createElement("div");
                        item.className  = "report-item";
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
                                ${tInfo ? `<div class="tcard-precio" style="margin-top:6px;">${formatearPrecio(tInfo.precio)}</div>` : ''}
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
 
                document.getElementById("edit-id").value             = cita.id;
                document.getElementById("titulo-agendar").innerText  = "Modificar / Reprogramar Cita";
                document.getElementById("fecha").value               = cita.fecha;
                document.getElementById("hora-seleccionada").value   = cita.hora;
 
                tratamientoSeleccionado = TRATAMIENTOS.find(
                    t => t.nombre.toLowerCase() === cita.tratamiento.toLowerCase()
                ) || TRATAMIENTOS[0];
 
                document.getElementById("trat-icon-header").innerText     = cita.tratamientoIcono;
                document.getElementById("trat-nombre-header").innerText   = cita.tratamiento;
                document.getElementById("trat-duracion-header").innerText = tratamientoSeleccionado.duracion;
                document.getElementById("trat-precio-header").innerText   = formatearPrecio(tratamientoSeleccionado.precio);
 
                // Cargar la lista de candidatos para este tratamiento
                // (ya no se fija el doctor original — al reprogramar, el
                // backend puede reasignar a quien esté libre en la nueva hora).
                cargarCandidatosTratamiento(tratamientoSeleccionado.nombre)
                    .then(() => {
                        actualizarAgenda();
                    });
 
                cambiarVista('agendar');
            }
        })
        .catch(err => console.error("Error al cargar cita:", err));
}
 
// =========================================================================
// ─── CANCELACIÓN CON MOTIVO
// =========================================================================
function eliminarCita(idCita) {
    document.getElementById("modal-cancelacion-id").value           = idCita;
    document.getElementById("motivo-cancelacion-texto").value       = "";
    document.getElementById("modal-cancelacion-error").style.display = "none";
    document.getElementById("modal-cancelacion").style.display      = "flex";
}
 
function cerrarModalCancelacion() {
    document.getElementById("modal-cancelacion").style.display = "none";
}
 
function confirmarCancelacion() {
    const idCita = document.getElementById("modal-cancelacion-id").value;
    const motivo = document.getElementById("motivo-cancelacion-texto").value.trim();
    const errEl  = document.getElementById("modal-cancelacion-error");
 
    if (!motivo) {
        errEl.innerText        = "⚠️ Por favor escribe el motivo de cancelación.";
        errEl.style.display    = "block";
        return;
    }
    errEl.style.display = "none";
 
    fetch(`${API_URL}?action=cancelar_cita`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_cita: idCita, motivo_cancelacion: motivo })
    })
    .then(res => res.json())
    .then(data => {
        cerrarModalCancelacion();
        if (data.status === "success") {
            mostrarToast("✅ Cita cancelada exitosamente.");
            renderLista();
        } else {
            mostrarToast("❌ " + data.message);
        }
    })
    .catch(err => console.error("Error al cancelar cita:", err));
}
 
// =========================================================================
// ─── TOAST
// =========================================================================
function mostrarToast(mensaje) {
    const toast   = document.getElementById("toast");
    toast.innerText = mensaje;
    toast.classList.add("visible");
    setTimeout(() => toast.classList.remove("visible"), 3500);
}
 
// =========================================================================
// ─── CERRAR SESIÓN
// =========================================================================
function cerrarSesion() {
    fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '/web/login/login.html')
        .catch(() => window.location.href = '/web/login/login.html');
}
 