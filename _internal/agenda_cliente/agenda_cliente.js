/**
 * CLINIDENT - Sistema de Agenda Interactiva (Módulo Paciente)
 * Archivo: agenda_cliente.js
 */

const API_URL = "/agenda_cliente/agenda_cliente";
let ID_USUARIO_LOGUEADO = null;


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
    fetch(`${API_URL}?action=get_sesion_usuario`)
        .then(res => res.json())
        .then(user => {
            if (user.status === "success") {
                ID_USUARIO_LOGUEADO = user.id;
                
                document.getElementById("nav-user-display").innerText = user.nombre;
                document.getElementById("nombre-usuario-bienvenida").innerText = user.nombre;
                
                // --- INICIO DE LÓGICA DE BOTÓN INTELIGENTE ---
                const btnVolver = document.getElementById("btn-volver-mi-panel");
                if (btnVolver) {
                    if (user.id_rol === 3) { // Recepcionista
                        btnVolver.style.display = "inline-block";
                        btnVolver.innerText = "📋 Volver a Recepción";
                        btnVolver.onclick = () => window.location.href = '../recepcionista/panel_rec.html';
                    } else if (user.id_rol === 1 || user.id_rol === 2) { // Admin u Odontólogo
                        btnVolver.style.display = "inline-block";
                        btnVolver.innerText = "🩺 Volver a Panel Médico";
                        btnVolver.onclick = () => window.location.href = '../odontologo/panel_medico.html';
                    }
                }
                // --- FIN DE LÓGICA DE BOTÓN INTELIGENTE ---

                cargarOdontologos();
            }
        })
        .catch(err => console.error("Error al obtener sesión:", err));
    
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
function cargarOdontologos() {
    fetch(`${API_URL}?action=get_odontologos`)
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                const selectDoc = document.getElementById("doc");
                if (!selectDoc) return;

                selectDoc.innerHTML = '<option value="">Seleccione un especialista</option>';
                
                response.data.forEach(doc => {
                    // 🚫 FILTRO ANTI-AUTOCONSULTA: 
                    // Si el ID del doctor coincide con el del usuario en sesión, no lo agregamos al selector
                    // Usamos == por seguridad por si uno es string y el otro number
                    if (doc.id == ID_USUARIO_LOGUEADO) {
                        return; // Salta este doctor y continúa con el siguiente del bucle
                    }

                    let option = document.createElement("option");
                    option.value = doc.id;
                    option.text = doc.nombre;
                    selectDoc.appendChild(option);
                });

                // Validación extra: Si el doctor se filtró y no quedaron más médicos en la lista
                if (selectDoc.options.length <= 1) {
                    selectDoc.innerHTML = '<option value="">No hay otros especialistas disponibles</option>';
                }
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
    selectDoc.selectedIndex = 0; // Por defecto

    // Búsqueda flexible e inteligente del especialista en el select
    for (let i = 0; i < selectDoc.options.length; i++) {
        let textoOpcion = selectDoc.options[i].text.toLowerCase().replace("dr. ", "").replace("dra. ", "").trim();
        let textoTratamiento = tratamientoSeleccionado.doctor.toLowerCase();
        
        if (textoOpcion !== "" && textoTratamiento.includes(textoOpcion)) {
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
    const doctorId = document.getElementById("doc").value;
    const editId = document.getElementById("edit-id").value;

    if (!fecha || !doctorId) return;

    let url = `${API_URL}?action=get_citas_ocupadas&fecha=${fecha}&doctor=${encodeURIComponent(doctorId)}`;
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
    const doctorId = document.getElementById("doc").value;
    const hora = document.getElementById("hora-seleccionada").value;

    if (!fecha || !hora || !doctorId) {
        mostrarToast("⚠️ Por favor selecciona fecha, horario y especialista.");
        return;
    }

    const payload = {
        edit_id: editId ? editId : null,
        doctor_id: doctorId,
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



// AGREGA ESTO AL FINAL DE TU AGENDA_CLIENTE.JS
function cerrarSesion() {
    if (!confirm("¿Estás seguro de que deseas cerrar tu sesión actual?")) return;

    // Petición al servidor para destruir las cookies de sesión
    fetch('/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Redirección directa a la pantalla de login
            window.location.href = '/web/login/login.html';
        }
    })
    .catch(err => {
        console.error("Error al cerrar sesión:", err);
        // Si falla la red, forzamos la salida de todos modos
        window.location.href = '/web/login/login.html';
    });
}

// ─── DIRECCIONAMIENTO A VISTA MÉDICA ───
function irAModoMedico() {
    // Redirecciona de vuelta al panel del especialista
    window.location.href = '../odontologo/panel_medico.html';
}