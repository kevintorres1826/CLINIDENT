/**
 * CLINIDENT - Dashboard de Recepción
 * Flujo: tratamiento → doctores dinámicos → grid de slots → confirmar
 */

const HORARIOS_MAESTROS = [
    "08:00 AM", "08:45 AM", "09:30 AM", "10:15 AM", "11:00 AM", "11:45 AM",
    "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM"
];

let horaSeleccionada = null;

document.addEventListener("DOMContentLoaded", () => {
    cargarSesion();
    document.getElementById("fecha").min = new Date().toISOString().split('T')[0];

    // Cuando cambia el tratamiento → recargar doctores y limpiar slots
    document.getElementById("tratamiento").addEventListener("change", () => {
        horaSeleccionada = null;
        document.getElementById("hora-seleccionada").value = "";
        cargarDoctoresPorTratamiento();
        actualizarSlots();
    });

    // Cuando cambia fecha → refrescar slots
    document.getElementById("fecha").addEventListener("change", actualizarSlots);

    // Cuando cambia paciente existente → refrescar slots (para bloquear sus citas)
    document.getElementById("selector_paciente").addEventListener("change", (e) => {
        const cajaNuevo = document.getElementById("caja-nuevo-paciente");
        if (e.target.value === "nuevo") {
            cajaNuevo.classList.remove("oculta");
        } else {
            cajaNuevo.classList.add("oculta");
            limpiarCamposNuevo();
        }
        actualizarSlots();
    });

    document.getElementById("form-agenda-recepcion")
        .addEventListener("submit", procesarCita);
});

/* ─── SESIÓN ─── */
function cargarSesion() {
    fetch('/agenda_cliente/agenda_cliente?action=get_sesion_usuario')
        .then(r => r.json())
        .then(u => {
            if (u.status === "success")
                document.getElementById("nombre-recepcionista").innerText = u.nombre;
        });
}

/* ─── PACIENTES ─── */
function cargarPacientes() {
    fetch('/agenda_recepcion/pacientes')
        .then(r => r.json())
        .then(response => {
            if (response.status !== "success") return;
            const sel = document.getElementById("selector_paciente");
            sel.innerHTML = `
                <option value="">Seleccione un paciente...</option>
                <option value="nuevo" style="font-weight:bold;color:#0ea5e9;">➕ Registrar Paciente Nuevo</option>
            `;
            response.data.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id_usuario;
                opt.text  = `${p.nombre} ${p.apellido}${p.telefono ? ' — ' + p.telefono : ''}`;
                sel.appendChild(opt);
            });
        });
}

function limpiarCamposNuevo() {
    ["nombre","apellido","telefono"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });
}

/* ─── DOCTORES POR TRATAMIENTO ─── */
function cargarDoctoresPorTratamiento() {
    const tratamiento = document.getElementById("tratamiento").value;
    const infoDoc     = document.getElementById("info-doctor-asignado");

    if (!tratamiento) {
        infoDoc.innerText = "";
        return;
    }

    fetch(`/agenda_recepcion/odontologos_por_tratamiento?tratamiento=${encodeURIComponent(tratamiento)}`)
        .then(r => r.json())
        .then(response => {
            if (response.status === "success" && response.data.length > 0) {
                const nombres = response.data.map(d => d.nombre).join(", ");
                infoDoc.innerText = `🩺 Especialistas disponibles: ${nombres}`;
            } else {
                infoDoc.innerText = "⚠️ Sin especialistas registrados para este tratamiento.";
            }
        });
}

/* ─── GRID DE SLOTS ─── */
function actualizarSlots() {
    const fecha       = document.getElementById("fecha").value;
    const tratamiento = document.getElementById("tratamiento").value;
    const grid        = document.getElementById("grid-horas");

    if (!fecha || !tratamiento) {
        grid.innerHTML = '<p style="color:#94a3b8;font-size:0.9rem;">Selecciona tratamiento y fecha para ver disponibilidad.</p>';
        return;
    }

    const selectPac = document.getElementById("selector_paciente").value;
    const idPac     = (selectPac && selectPac !== "nuevo") ? selectPac : "";

    let url = `/agenda_recepcion/horas_ocupadas?fecha=${fecha}&tratamiento=${encodeURIComponent(tratamiento)}`;
    if (idPac) url += `&id_paciente=${idPac}`;

    fetch(url)
        .then(r => r.json())
        .then(response => {
            if (response.status !== "success") return;
            renderSlots(response.data);
        });
}

function renderSlots(ocupadas) {
    const grid = document.getElementById("grid-horas");
    grid.innerHTML = "";

    HORARIOS_MAESTROS.forEach(hora => {
        const slot     = document.createElement("div");
        slot.className = "hora-slot";
        slot.innerText = hora;

        if (ocupadas.includes(hora)) {
            slot.classList.add("occupied");
        } else {
            if (hora === horaSeleccionada) slot.classList.add("selected");
            slot.onclick = () => seleccionarSlot(slot, hora);
        }
        grid.appendChild(slot);
    });
}

function seleccionarSlot(el, hora) {
    document.querySelectorAll(".hora-slot").forEach(s => s.classList.remove("selected"));
    el.classList.add("selected");
    horaSeleccionada = hora;
    document.getElementById("hora-seleccionada").value = hora;
}

/* ─── NAVEGACIÓN ─── */
function cambiarVista(vista) {
    const panel  = document.getElementById('vista-panel');
    const agenda = document.getElementById('vista-agenda');
    const btnV   = document.getElementById('btn-volver-panel');
    const btnS   = document.getElementById('btn-logout');

    if (vista === 'agenda') {
        panel.classList.add('oculta');
        agenda.classList.remove('oculta');
        btnS.classList.add('oculta');
        btnV.classList.remove('oculta');
        cargarPacientes();
        // Resetear estado del formulario
        horaSeleccionada = null;
        document.getElementById("hora-seleccionada").value = "";
        document.getElementById("grid-horas").innerHTML =
            '<p style="color:#94a3b8;font-size:0.9rem;">Selecciona tratamiento y fecha para ver disponibilidad.</p>';
        document.getElementById("info-doctor-asignado").innerText = "";
    } else {
        panel.classList.remove('oculta');
        agenda.classList.add('oculta');
        btnS.classList.remove('oculta');
        btnV.classList.add('oculta');
        document.getElementById("form-agenda-recepcion").reset();
        document.getElementById("caja-nuevo-paciente").classList.add("oculta");
        horaSeleccionada = null;
    }
}

function cerrarSesionRecepcionista() {
    if (!confirm("¿Deseas cerrar sesión?")) return;
    fetch('/logout', { method: 'POST' })
        .then(() => window.location.href = '../login/login.html');
}

function toggleVistaPaciente() {
    window.location.href = '../agenda_cliente/index.html';
}

/* ─── ENVÍO ─── */
function procesarCita(e) {
    e.preventDefault();

    const selectPac = document.getElementById("selector_paciente").value;
    const esNuevo   = selectPac === "nuevo";
    const hora      = document.getElementById("hora-seleccionada").value;

    if (!hora) {
        alert("⚠️ Selecciona un horario disponible.");
        return;
    }

    const payload = {
        id_usuario_existente: esNuevo ? null : parseInt(selectPac),
        nombre:      esNuevo ? document.getElementById("nombre").value.trim()    : "",
        apellido:    esNuevo ? document.getElementById("apellido").value.trim()  : "",
        telefono:    esNuevo ? document.getElementById("telefono").value.trim()  : "",
        tratamiento: document.getElementById("tratamiento").value,
        fecha:       document.getElementById("fecha").value,
        hora:        hora
    };

    fetch('/agenda_recepcion/agendar', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        alert(data.message);
        if (data.status === "success") cambiarVista('panel');
    })
    .catch(() => alert("❌ Error de comunicación con el servidor."));
}