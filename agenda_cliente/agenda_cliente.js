/**
 * CLINIDENT - Sistema de Agenda Interactiva (Módulo Paciente)
 * Archivo: agenda_cliente.js
 */

const API_URL = "agenda_cliente.php";

// Catálogo de Tratamientos del Sistema
const TRATAMIENTOS = [
    { id: "limpieza", nombre: "Limpieza Dental", desc: "Profilaxis profunda y eliminación de sarro bacteriano.", duracion: "45 MIN", doctor: "Dr. Alberto Casas (General)", icono: "🦷" },
    { id: "revision", nombre: "Revisión General", desc: "Evaluación integral de salud oral y diagnóstico.", duracion: "30 MIN", doctor: "Dr. Alberto Casas (General)", icono: "🩺" },
    { id: "ortodoncia", nombre: "Ortodoncia", desc: "Ajuste y control de aparatología o brackets.", duracion: "60 MIN", doctor: "Dra. Elena Marín (Ortodoncia)", icono: "😁" },
    { id: "endodoncia", nombre: "Endodoncia", desc: "Tratamiento de conductos radiculares y alivio del dolor.", duracion: "90 MIN", doctor: "Dr. Camilo Ruiz (Cirugía)", icono: "💉" },
    { id: "cirugia", nombre: "Cirugía Oral", desc: "Extracciones complejas y procedimientos quirúrgicos.", duracion: "120 MIN", doctor: "Dr. Camilo Ruiz (Cirugía)", icono: "🔬" }
];

// Listado Maestro de Horarios Habilitados en la Clínica
const HORARIOS_MAESTROS = [
    "08:00 AM", "08:45 AM", "09:30 AM", "10:15 AM", "11:00 AM", "11:45 AM",
    "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM"
];

let tratamientoSeleccionado = null;

// =========================================================================
// ─── INICIALIZACIÓN Y VALIDACIÓN DE SESIÓN REAL
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    // Sincronizar dinámicamente con el Login real de PHP de XAMPP
    fetch(`${API_URL}?action=get_sesion_usuario`)
        .then(res => res.json())
        .then(user => {
            if (user.status === "success") {
                document.getElementById("nav-user-display").innerText = user.nombre;
                document.getElementById("nombre-usuario-bienvenida").innerText = user.nombre;
            }
        })
        .catch(err => console.error("Error al obtener sesión:", err));
    
    // Bloquear fechas pasadas en el calendario
    const inputFecha = document.getElementById("fecha");
    if(inputFecha) {
        const hoy = new Date().toISOString().split('T')[0];
        inputFecha.min = hoy;
    }

    cambiarVista('menu');
});

function cambiarVista(vistaId) {
    document.querySelectorAll('.view').forEach(v => {
        v.classList.remove('active');
    });
    const vistaDestino = document.getElementById(`view-${vistaId}`);
    if (vistaDestino) {
        vistaDestino.classList.add('active');
    }
}

// =========================================================================
// ─── FLUJO: TRATAMIENTOS (PANTALLA 1)
// =========================================================================
function abrirSelectorTratamiento() {
    document.getElementById("edit-id").value = "";
    document.getElementById("titulo-agendar").innerText = "Planifica tu visita";
    tratamientoSeleccionado = null;

    const grid = document.getElementById("grid-tratamientos");
    grid.innerHTML = "";

    TRATAMIENTOS.forEach(t => {
        const card = document.createElement("div");
        card.className = "tratamiento-card";
        card.id = `tcard-${t.id}`;
        card.onclick = () => seleccionarTratamientoCard(t);

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

    document.getElementById("trat-icon-header").innerText = tratamientoSeleccionado.icono;
    document.getElementById("trat-nombre-header").innerText = tratamientoSeleccionado.nombre;
    document.getElementById("trat-duracion-header").innerText = tratamientoSeleccionado.duracion;
    document.getElementById("trat-doctor-header").innerText = tratamientoSeleccionado.doctor;

    const selectDoc = document.getElementById("doc");
    for (let i = 0; i < selectDoc.options.length; i++) {
        if (selectDoc.options[i].text.includes(tratamientoSeleccionado.doctor)) {
            selectDoc.selectedIndex = i;
            break;
        }
    }

    const inputFecha = document.getElementById("fecha");
    if (!inputFecha.value) {
        inputFecha.value = new Date().toISOString().split('T')[0];
    }

    document.getElementById("hora-seleccionada").value = "";
    actualizarAgenda();
    cambiarVista('agendar');
}

function volverATratamiento() {
    cambiarVista('tratamiento');
}

// =========================================================================
// ─── FLUJO: DISPONIBILIDAD HORARIA CORREGIDA (PANTALLA 2)
// =========================================================================
function actualizarAgenda() {
    const fecha = document.getElementById("fecha").value;
    const doctor = document.getElementById("doc").value;
    const editId = document.getElementById("edit-id").value;

    if (!fecha) return;

    // Enviamos el editId al backend para liberar la propia hora de la cita en edición
    let url = `${API_URL}?action=get_citas_ocupadas&fecha=${fecha}&doctor=${encodeURIComponent(doctor)}`;
    if (editId) {
        url += `&edit_id=${editId}`;
    }

    fetch(url)
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                renderSlotsHorarios(response.data);
            } else {
                mostrarToast("Error al mapear franjas horarias.");
            }
        })
        .catch(err => console.error(err));
}

function renderSlotsHorarios(horasOcupadas) {
    const gridHoras = document.getElementById("grid-horas");
    gridHoras.innerHTML = "";
    
    const horaSeleccionadaPrevia = document.getElementById("hora-seleccionada").value;

    HORARIOS_MAESTROS.forEach(hora => {
        const slot = document.createElement("div");
        slot.className = "hora-slot";
        slot.innerText = hora;

        const estaOcupada = horasOcupadas.includes(hora);

        if (estaOcupada) {
            slot.classList.add("occupied");
        } else {
            if (hora === horaSeleccionadaPrevia) {
                slot.classList.add("selected");
            }
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
// ─── OPERACIONES POST Y ESCRITURA
// =========================================================================
function finalizarAgendado() {
    const editId = document.getElementById("edit-id").value;
    const fecha = document.getElementById("fecha").value;
    const doctor = document.getElementById("doc").value;
    const hora = document.getElementById("hora-seleccionada").value;

    if (!fecha || !hora) {
        mostrarToast("⚠️ Por favor selecciona una fecha y horario.");
        return;
    }

    const payload = {
        edit_id: editId ? editId : null,
        doctor: doctor,
        fecha: fecha,
        hora: hora,
        tratamiento: tratamientoSeleccionado ? tratamientoSeleccionado.nombre : "Limpieza Dental"
    };

    fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            mostrarToast(editId ? "¡Cita reprogramada con éxito!" : "¡Cita médica guardada correctamente! 🎉");
            setTimeout(() => {
                renderLista();
                cambiarVista('menu');
            }, 1300);
        } else {
            mostrarToast("❌ " + data.message);
        }
    })
    .catch(err => console.error(err));
}

// =========================================================================
// ─── HISTORIAL CLÍNICO Y EDICIÓN
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
                    contenedor.innerHTML = '<div class="empty-msg">No registras citas médicas activas.</div>';
                    return;
                }

                citas.forEach(c => {
                    const fPartes = c.fecha.split("-");
                    const fechaLegible = fPartes.length === 3 ? `${fPartes[2]}/${fPartes[1]}/${fPartes[0]}` : c.fecha;

                    const item = document.createElement("div");
                    item.className = "report-item";
                    item.innerHTML = `
                        <div class="tcard-info">
                            <div class="tcard-nombre">${c.tratamientoIcono} ${c.tratamiento}</div>
                            <div class="tcard-desc" style="margin-top:4px;">Especialista: <strong>${c.doctor}</strong></div>
                            <div class="tcard-duracion" style="margin-top:4px; color:var(--text-primary);">📅 ${fechaLegible} &nbsp;|&nbsp; ⏱ ${c.hora}</div>
                        </div>
                        <div class="actions-btns">
                            <button class="btn-edit" onclick="iniciarEdicion(${c.id})">Reprogramar</button>
                            <button class="btn-cancel-cita" onclick="eliminarCita(${c.id})">Cancelar</button>
                        </div>
                    `;
                    contenedor.appendChild(item);
                });
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

                document.getElementById("edit-id").value = cita.id;
                document.getElementById("titulo-agendar").innerText = "Modificar / Reprogramar Cita";
                document.getElementById("fecha").value = cita.fecha;
                document.getElementById("hora-seleccionada").value = cita.hora;

                tratamientoSeleccionado = TRATAMIENTOS.find(t => t.nombre === cita.tratamiento) || TRATAMIENTOS[0];

                document.getElementById("trat-icon-header").innerText = cita.tratamientoIcono;
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
    if (!confirm("¿Seguro que deseas cancelar esta cita? El horario se liberará inmediatamente.")) return;

    fetch(`${API_URL}?action=cancelar_cita`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_cita: idCita })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            mostrarToast("Cita cancelada correctamente.");
            renderLista();
        }
    })
    .catch(err => console.error(err));
}

function mostrarToast(mensaje) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = mensaje;
    toast.classList.add("show");
    setTimeout(() => { toast.classList.remove("show"); }, 3500);
}