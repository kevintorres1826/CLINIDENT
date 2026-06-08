/**
 * CLINIDENT - Lógica unificada para el Dashboard de Recepción
 */

document.addEventListener("DOMContentLoaded", () => {
    cargarSesion();
    cargarOdontologos();
    
    // Configurar fecha mínima al día de hoy
    document.getElementById("fecha").min = new Date().toISOString().split('T')[0];

    // Lógica del selector inteligente de pacientes
    document.getElementById("selector_paciente").addEventListener("change", (e) => {
        const cajaNuevo = document.getElementById("caja-nuevo-paciente");
        const inputNombre = document.getElementById("nombre");
        const inputApellido = document.getElementById("apellido");

        if (e.target.value === "nuevo") {
            cajaNuevo.classList.remove("oculta");
            inputNombre.required = true;
            inputApellido.required = true;
        } else {
            cajaNuevo.classList.add("oculta");
            inputNombre.required = false;
            inputApellido.required = false;
            inputNombre.value = "";
            inputApellido.value = "";
        }
    });

    // Enviar formulario
    document.getElementById("form-agenda-recepcion").addEventListener("submit", procesarCita);
});

/* ─── FUNCIONES DE CARGA ─── */
function cargarSesion() {
    fetch('/agenda_cliente/agenda_cliente?action=get_sesion_usuario')
        .then(res => res.json())
        .then(user => {
            if (user.status === "success") {
                document.getElementById("nombre-recepcionista").innerText = user.nombre;
            }
        }).catch(err => console.error(err));
}

function cargarOdontologos() {
    fetch('/agenda_cliente/agenda_cliente?action=get_odontologos')
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                const selectDoc = document.getElementById("id_odontologo");
                response.data.forEach(doc => {
                    let option = document.createElement("option");
                    option.value = doc.id;
                    option.text = doc.nombre;
                    selectDoc.appendChild(option);
                });
            }
        }).catch(err => console.error(err));
}

function cargarPacientes() {
    fetch('/agenda_recepcion/pacientes')
        .then(res => res.json())
        .then(response => {
            if (response.status === "success") {
                const selectPac = document.getElementById("selector_paciente");
                selectPac.innerHTML = `<option value="">Seleccione un paciente...</option>
                                       <option value="nuevo" style="font-weight: bold; color: #0ea5e9;">➕ Registrar Paciente Nuevo</option>`;
                
                response.data.forEach(pac => {
                    let option = document.createElement("option");
                    option.value = pac.id_usuario;
                    // Mostramos nombre, apellido y correo
                    option.text = `${pac.nombre} ${pac.apellido} - ${pac.correo || 'Sin correo'}`;
                    selectPac.appendChild(option);
                });
            }
        }).catch(err => console.error(err));
}

/* ─── NAVEGACIÓN SPA ─── */
function cambiarVista(vista) {
    const vistaPanel = document.getElementById('vista-panel');
    const vistaAgenda = document.getElementById('vista-agenda');
    const btnVolver = document.getElementById('btn-volver-panel');
    const btnSalir = document.getElementById('btn-logout');

    if (vista === 'agenda') {
        vistaPanel.classList.add('oculta');
        vistaAgenda.classList.remove('oculta');
        btnSalir.classList.add('oculta');
        btnVolver.classList.remove('oculta');
        cargarPacientes(); // Refrescamos lista por si alguien creó un usuario en otro lado
    } else {
        vistaPanel.classList.remove('oculta');
        vistaAgenda.classList.add('oculta');
        btnSalir.classList.remove('oculta');
        btnVolver.classList.add('oculta');
        
        // Limpiamos el formulario
        document.getElementById("form-agenda-recepcion").reset();
        document.getElementById("caja-nuevo-paciente").classList.add("oculta");
    }
}

function cerrarSesionRecepcionista() {
    if (!confirm("¿Estás seguro de que deseas salir del panel de recepción?")) return;
    fetch('/logout', { method: 'POST' }).then(() => window.location.href = '../login/login.html');
}

/* ─── PROCESAMIENTO FINAL ─── */
function procesarCita(e) {
    e.preventDefault();

    const selectPaciente = document.getElementById("selector_paciente").value;
    
    const payload = {
        id_usuario_existente: selectPaciente !== "nuevo" ? parseInt(selectPaciente) : null,
        nombre: selectPaciente === "nuevo" ? document.getElementById("nombre").value : "",
        apellido: selectPaciente === "nuevo" ? document.getElementById("apellido").value : "",
        id_odontologo: parseInt(document.getElementById("id_odontologo").value),
        tratamiento: document.getElementById("tratamiento").value,
        fecha: document.getElementById("fecha").value,
        hora: document.getElementById("hora").value
    };

    fetch('/agenda_recepcion/agendar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        if (data.status === "success") {
            cambiarVista('panel');
        }
    })
    .catch(err => {
        console.error(err);
        alert("❌ Error de comunicación con el servidor.");
    });
}

function toggleVistaPaciente() {
    window.location.href = '../agenda_cliente/index.html';
}