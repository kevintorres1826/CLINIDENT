const horarios = ["08:00 AM","08:30 AM","09:00 AM","09:30 AM","10:00 AM","10:30 AM","11:00 AM","11:30 AM","01:00 PM","01:30 PM","02:00 PM","02:30 PM","03:00 PM","03:30 PM","04:00 PM","04:30 PM","05:00 PM"];

// ─── CATÁLOGO DE TRATAMIENTOS ───
const tratamientos = [
    {
        id: "limpieza",
        nombre: "Limpieza Dental",
        descripcion: "Profilaxis y eliminación de sarro",
        icono: "🦷",
        duracion: "45 min",
        doctor: "Dr. Alberto Casas (General)"
    },
    {
        id: "ortodoncia",
        nombre: "Ortodoncia",
        descripcion: "Brackets, alineadores y correcciones",
        icono: "😁",
        duracion: "60 min",
        doctor: "Dra. Elena Marín (Ortodoncia)"
    },
    {
        id: "blanqueamiento",
        nombre: "Blanqueamiento",
        descripcion: "Blanqueamiento dental profesional",
        icono: "✨",
        duracion: "90 min",
        doctor: "Dr. Alberto Casas (General)"
    },
    {
        id: "cirugia",
        nombre: "Cirugía Oral",
        descripcion: "Extracciones y procedimientos quirúrgicos",
        icono: "🔬",
        duracion: "120 min",
        doctor: "Dr. Camilo Ruiz (Cirugía)"
    },
    {
        id: "endodoncia",
        nombre: "Endodoncia",
        descripcion: "Tratamiento de conductos radiculares",
        icono: "💉",
        duracion: "90 min",
        doctor: "Dr. Camilo Ruiz (Cirugía)"
    },
    {
        id: "revision",
        nombre: "Revisión General",
        descripcion: "Chequeo y diagnóstico completo",
        icono: "🩺",
        duracion: "30 min",
        doctor: "Dr. Alberto Casas (General)"
    }
];

// ─── ESTADO DEL FLUJO NUEVO ───
let tratamientoSeleccionado = null;
let usuarioLogueado = "Paciente"; // Valor por defecto inicial

// ─── BASE DE DATOS LOCAL (localStorage) ───
function getCitas() {
    return JSON.parse(localStorage.getItem('clinident_citas') || '[]');
}

function saveCitas(citas) {
    localStorage.setItem('clinident_citas', JSON.stringify(citas));
}

// ─── NAVEGACIÓN ───
function cambiarVista(id) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view-' + id).classList.add('active');
}

// ─── FLUJO NUEVO: PASO 1 - SELECCIONAR TRATAMIENTO ───
function abrirSelectorTratamiento() {
    tratamientoSeleccionado = null;
    document.getElementById('edit-id').value = '';
    renderTratamientos();
    cambiarVista('tratamiento');
}

function renderTratamientos() {
    const grid = document.getElementById('grid-tratamientos');
    grid.innerHTML = tratamientos.map(t => `
        <div class="tratamiento-card" id="tcard-${t.id}" onclick="seleccionarTratamiento('${t.id}')">
            <div class="tcard-icon">${t.icono}</div>
            <div class="tcard-info">
                <div class="tcard-nombre">${t.nombre}</div>
                <div class="tcard-desc">${t.descripcion}</div>
                <div class="tcard-duracion">⏱ ${t.duracion}</div>
            </div>
            <div class="tcard-check" id="check-${t.id}">✓</div>
        </div>
    `).join('');
}

function seleccionarTratamiento(id) {
    tratamientoSeleccionado = tratamientos.find(t => t.id === id);

    // highlight visual
    document.querySelectorAll('.tratamiento-card').forEach(c => c.classList.remove('selected'));
    document.querySelectorAll('.tcard-check').forEach(c => c.classList.remove('visible'));
    document.getElementById('tcard-' + id).classList.add('selected');
    document.getElementById('check-' + id).classList.add('visible');

    // habilitar botón continuar
    const btn = document.getElementById('btn-continuar-trat');
    btn.disabled = false;
    btn.classList.add('ready');
}

// ... (El resto de tus funciones se mantienen idénticas para no romper tu lógica) ...
function confirmarTratamiento() {
    if (!tratamientoSeleccionado) {
        alert("⚠️ Por favor selecciona un tipo de tratamiento.");
        return;
    }
    prepararAgendadoConTratamiento();
}

function prepararAgendadoConTratamiento() {
    const t = tratamientoSeleccionado;
    document.getElementById('trat-nombre-header').innerText = t.nombre;
    document.getElementById('trat-icon-header').innerText = t.icono;
    document.getElementById('trat-duracion-header').innerText = t.duracion;
    document.getElementById('trat-doctor-header').innerText = t.doctor;
    document.getElementById('doc').value = t.doctor;
    document.getElementById('edit-id').value = '';
    document.getElementById('hora-seleccionada').value = '';
    document.getElementById('titulo-agendar').innerText = 'Selecciona Fecha y Hora';
    document.getElementById('btn-save').innerText = 'Confirmar Cita';
    document.getElementById('fecha').valueAsDate = new Date();
    cambiarVista('agendar');
    actualizarAgenda();
}

function prepararAgendado() { abrirSelectorTratamiento(); }

function actualizarAgenda() {
    const grid = document.getElementById('grid-horas');
    const doctor = document.getElementById('doc').value;
    const fecha = document.getElementById('fecha').value;
    const editId = document.getElementById('edit-id').value;
    const citas = getCitas();
    const ocupadas = citas.filter(c => c.doctor === doctor && c.fecha === fecha && c.id !== editId).map(c => c.hora);

    grid.innerHTML = '';
    horarios.forEach(h => {
        const div = document.createElement('div');
        div.className = 'hora-slot';
        div.innerText = h;
        if (ocupadas.includes(h)) {
            div.classList.add('occupied');
        } else {
            if (document.getElementById('hora-seleccionada').value === h) { div.classList.add('selected'); }
            div.onclick = function () {
                document.querySelectorAll('.hora-slot').forEach(s => s.classList.remove('selected'));
                this.classList.add('selected');
                document.getElementById('hora-seleccionada').value = h;
            };
        }
        grid.appendChild(div);
    });
}

function finalizarAgendado() {
    const doctor = document.getElementById('doc').value;
    const fecha = document.getElementById('fecha').value;
    const hora = document.getElementById('hora-seleccionada').value;
    const editId = document.getElementById('edit-id').value;

    if (!fecha || !hora) {
        alert("⚠️ Por favor selecciona una fecha y haz clic en una hora.");
        return;
    }

    const citas = getCitas();
    if (editId) {
        const idx = citas.findIndex(c => c.id === editId);
        if (idx !== -1) {
            citas[idx].doctor = doctor;
            citas[idx].fecha = fecha;
            citas[idx].hora = hora;
            if (tratamientoSeleccionado) {
                citas[idx].tratamiento = tratamientoSeleccionado.nombre;
                citas[idx].tratamientoIcono = tratamientoSeleccionado.icono;
            }
        }
    } else {
        const nueva = {
            id: Date.now().toString(),
            paciente: usuarioLogueado, // Usará el primer nombre extraído abajo
            doctor,
            fecha,
            hora,
            tratamiento: tratamientoSeleccionado ? tratamientoSeleccionado.nombre : 'General',
            tratamientoIcono: tratamientoSeleccionado ? tratamientoSeleccionado.icono : '🦷'
        };
        citas.push(nueva);
    }
    saveCitas(citas);
    mostrarToast(editId ? '✏️ Cita actualizada' : '✅ ¡Cita confirmada!');
    tratamientoSeleccionado = null;
    cambiarVista('menu');
}

function renderLista() {
    const citas = getCitas();
    const contenedor = document.getElementById('lista-citas');
    if (citas.length === 0) {
        contenedor.innerHTML = '<div class="empty-msg">📭 No hay citas registradas aún.</div>';
        return;
    }
    citas.sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora));
    contenedor.innerHTML = citas.map(c => `
        <div class="report-item">
            <div>
                <div style="font-weight:800; font-size:1.1rem;">${c.tratamientoIcono || '🦷'} ${c.tratamiento || 'Consulta'}</div>
                <div style="color:#64748b; margin-top:4px;">👤 ${c.paciente} &nbsp;|&nbsp; 🩺 ${c.doctor}</div>
                <div style="color:#64748b; margin-top:2px;">📅 ${formatFecha(c.fecha)} — ⏰ ${c.hora}</div>
            </div>
            <div class="actions-btns">
                <button class="btn-edit" onclick="editarCita('${c.id}')">✏️ Editar</button>
                <button class="btn-cancel-cita" onclick="eliminarCita('${c.id}')">🗑️ Cancelar</button>
            </div>
        </div>
    `).join('');
}

function formatFecha(fechaStr) {
    if (!fechaStr) return '';
    const [y, m, d] = fechaStr.split('-');
    return `${d}/${m}/${y}`;
}

function editarCita(id) {
    const citas = getCitas();
    const cita = citas.find(c => c.id === id);
    if (!cita) return;
    tratamientoSeleccionado = tratamientos.find(t => t.nombre === cita.tratamiento) || null;
    document.getElementById('edit-id').value = cita.id;
    document.getElementById('doc').value = cita.doctor;
    document.getElementById('fecha').value = cita.fecha;
    document.getElementById('hora-seleccionada').value = cita.hora;
    document.getElementById('titulo-agendar').innerText = '✏️ Editar Cita';
    document.getElementById('btn-save').innerText = 'Guardar Cambios';
    document.getElementById('trat-nombre-header').innerText = cita.tratamiento || 'Consulta';
    document.getElementById('trat-icon-header').innerText = cita.tratamientoIcono || '🦷';
    document.getElementById('trat-duracion-header').innerText = tratamientoSeleccionado ? tratamientoSeleccionado.duracion : '—';
    document.getElementById('trat-doctor-header').innerText = cita.doctor;
    cambiarVista('agendar');
    actualizarAgenda();
}

function eliminarCita(id) {
    if (!confirm('¿Seguro que deseas cancelar esta cita?')) return;
    const citas = getCitas().filter(c => c.id !== id);
    saveCitas(citas);
    mostrarToast('🗑️ Cita cancelada');
    renderLista();
}

function mostrarToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function cancelarEdicion() { tratamientoSeleccionado = null; cambiarVista('menu'); }
function volverATratamiento() { cambiarVista('tratamiento'); }


// ─── 🆕 SECCIÓN DEFENSIVA AL CARGAR LA PÁGINA ───
document.addEventListener("DOMContentLoaded", () => {
    // 1. Ir a buscar el nombre guardado por el login
    let nombreGuardado = localStorage.getItem('clinident_usuario_nombre');
    
    // 2. Si existe un nombre real, procesarlo
    if (nombreGuardado && nombreGuardado.trim() !== "") {
        usuarioLogueado = nombreGuardado.trim().split(" ")[0];
    } else {
        usuarioLogueado = "Paciente";
    }
    
    // 3. Pintarlo en el HTML de forma obligatoria
    const elBienvenida = document.getElementById('nombre-usuario-bienvenida');
    if (elBienvenida) {
        elBienvenida.innerText = usuarioLogueado;
    }
});