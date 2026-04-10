const horarios = ["08:00 AM","08:30 AM","09:00 AM","09:30 AM","10:00 AM","10:30 AM","11:00 AM","11:30 AM","01:00 PM","01:30 PM","02:00 PM","02:30 PM","03:00 PM","03:30 PM","04:00 PM","04:30 PM","05:00 PM"];

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

function prepararAgendado() {
    document.getElementById('edit-id').value = '';
    document.getElementById('hora-seleccionada').value = '';
    document.getElementById('titulo-agendar').innerText = 'Configurar Agendamiento';
    document.getElementById('btn-save').innerText = 'Confirmar Espacio Médico';
    document.getElementById('fecha').valueAsDate = new Date();
    cambiarVista('agendar');
    actualizarAgenda();
}

// ─── GRILLA DE HORAS ───
function actualizarAgenda() {
    const grid = document.getElementById('grid-horas');
    const doctor = document.getElementById('doc').value;
    const fecha = document.getElementById('fecha').value;
    const editId = document.getElementById('edit-id').value;
    const citas = getCitas();

    const ocupadas = citas
        .filter(c => c.doctor === doctor && c.fecha === fecha && c.id !== editId)
        .map(c => c.hora);

    grid.innerHTML = '';
    horarios.forEach(h => {
        const div = document.createElement('div');
        div.className = 'hora-slot';
        div.innerText = h;

        if (ocupadas.includes(h)) {
            div.classList.add('occupied');
            div.title = 'Hora ocupada';
        } else {
            if (document.getElementById('hora-seleccionada').value === h) {
                div.classList.add('selected');
            }
            div.onclick = function () {
                document.querySelectorAll('.hora-slot').forEach(s => s.classList.remove('selected'));
                this.classList.add('selected');
                document.getElementById('hora-seleccionada').value = h;
            };
        }
        grid.appendChild(div);
    });
}

// ─── GUARDAR CITA ───
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
        }
    } else {
        const nueva = {
            id: Date.now().toString(),
            paciente: 'Nico', // En un sistema real, aquí iría el nombre del paciente logueado
            doctor,
            fecha,
            hora
        };
        citas.push(nueva);
    }

    saveCitas(citas);
    mostrarToast(editId ? '✏️ Cita actualizada' : '✅ ¡Cita guardada!');
    cambiarVista('menu');
}

// ─── LISTA DE CITAS ───
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
                <div style="font-weight:800; font-size:1.1rem;">👤 ${c.paciente}</div>
                <div style="color:#64748b; margin-top:4px;">🩺 ${c.doctor}</div>
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

// ─── EDITAR Y ELIMINAR ───
function editarCita(id) {
    const citas = getCitas();
    const cita = citas.find(c => c.id === id);
    if (!cita) return;

    document.getElementById('edit-id').value = cita.id;
    document.getElementById('doc').value = cita.doctor;
    document.getElementById('fecha').value = cita.fecha;
    document.getElementById('hora-seleccionada').value = cita.hora;
    document.getElementById('titulo-agendar').innerText = '✏️ Editar Cita';
    document.getElementById('btn-save').innerText = 'Guardar Cambios';

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

function cancelarEdicion() { cambiarVista('menu'); }