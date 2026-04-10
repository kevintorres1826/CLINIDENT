const DOCTOR_NOMBRE = 'Dr. Alberto Casas (General)';

function getCitas() {
    return JSON.parse(localStorage.getItem('clinident_citas') || '[]');
}

function getAtendidos() {
    return JSON.parse(localStorage.getItem('clinident_atendidos') || '[]');
}

function saveAtendidos(lista) {
    localStorage.setItem('clinident_atendidos', JSON.stringify(lista));
}

function fechaHoy() {
    const hoy = new Date();
    const y = hoy.getFullYear();
    const m = String(hoy.getMonth() + 1).padStart(2, '0');
    const d = String(hoy.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function irHoy() {
    document.getElementById('filtro-fecha').value = fechaHoy();
    renderAgenda();
}

function formatFecha(fechaStr) {
    if (!fechaStr) return '';
    const [y, m, d] = fechaStr.split('-');
    return `${d}/${m}/${y}`;
}

function renderAgenda() {
    const fecha = document.getElementById('filtro-fecha').value;
    const citas = getCitas();
    const atendidos = getAtendidos();

    const citasDelDia = citas
        .filter(c => c.doctor === DOCTOR_NOMBRE && c.fecha === fecha)
        .sort((a, b) => convertirHora(a.hora) - convertirHora(b.hora));

    const pendientes = citasDelDia.filter(c => !atendidos.includes(c.id));
    const atendidasHoy = citasDelDia.filter(c => atendidos.includes(c.id));

    document.getElementById('stat-total').innerText = citasDelDia.length;
    document.getElementById('stat-pendientes').innerText = pendientes.length;
    document.getElementById('stat-atendidos').innerText = atendidasHoy.length;

    const lista = document.getElementById('lista-agenda');

    if (citasDelDia.length === 0) {
        lista.innerHTML = `<div class="empty-msg">📭 No hay citas agendadas para el ${formatFecha(fecha) || 'esta fecha'}.</div>`;
        return;
    }

    lista.innerHTML = citasDelDia.map(c => {
        const yaAtendido = atendidos.includes(c.id);
        return `
        <div class="cita-card">
            <div class="cita-hora">${c.hora}</div>
            <div class="cita-info">
                <div class="paciente">👤 ${c.paciente}</div>
                <div class="detalle">📅 ${formatFecha(c.fecha)}</div>
            </div>
            <span class="badge ${yaAtendido ? 'badge-atendido' : 'badge-pendiente'}">
                ${yaAtendido ? '✅ Atendido' : '⏳ Pendiente'}
            </span>
            <button class="btn-atender" onclick="marcarAtendido('${c.id}')" ${yaAtendido ? 'disabled' : ''}>
                ${yaAtendido ? 'Listo' : 'Marcar atendido'}
            </button>
        </div>`;
    }).join('');
}

function marcarAtendido(id) {
    const atendidos = getAtendidos();
    if (!atendidos.includes(id)) {
        atendidos.push(id);
        saveAtendidos(atendidos);
        mostrarToast('✅ Paciente marcado como atendido');
        renderAgenda();
    }
}

function convertirHora(horaStr) {
    const [time, period] = horaStr.split(' ');
    let [h, m] = time.split(':').map(Number);
    if (period === 'PM' && h !== 12) h += 12;
    if (period === 'AM' && h === 12) h = 0;
    return h * 60 + m;
}

function mostrarToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('filtro-fecha').value = fechaHoy();
    renderAgenda();
});