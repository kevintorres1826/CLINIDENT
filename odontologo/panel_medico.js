const API_URL = "/odontologo";
 
// ─── NAVEGACIÓN ENTRE VISTAS ───
 
function mostrarPanel() {
    document.getElementById('vista-panel').style.display = 'flex';
    document.getElementById('vista-agenda').style.display = 'none';
    document.getElementById('btn-volver').style.display = 'none';
}
 
function mostrarAgenda() {
    document.getElementById('vista-panel').style.display = 'none';
    document.getElementById('vista-agenda').style.display = 'block';
    document.getElementById('btn-volver').style.display = 'inline-block';
    document.getElementById('filtro-fecha').value = fechaHoy();
    renderAgenda();
}
 
// ─── UTILIDADES DE FECHA ───
 
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
 
// ─── AGENDA (consume el backend) ───
 
function renderAgenda() {
    const fecha = document.getElementById('filtro-fecha').value;
    const lista = document.getElementById('lista-agenda');
 
    lista.innerHTML = '<div class="empty-msg">Consultando base de datos...</div>';
 
    fetch(`${API_URL}/citas?fecha=${fecha}`, {
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== 'success') {
            lista.innerHTML = `<div class="empty-msg">❌ Error: ${data.message}</div>`;
            return;
        }
 
        const citas = data.citas;
 
        const pendientes = citas.filter(c => c.estado !== 'completada');
        const atendidas  = citas.filter(c => c.estado === 'completada');
 
        document.getElementById('stat-total').innerText      = citas.length;
        document.getElementById('stat-pendientes').innerText = pendientes.length;
        document.getElementById('stat-atendidos').innerText  = atendidas.length;
 
        if (citas.length === 0) {
            lista.innerHTML = `<div class="empty-msg">📭 No hay citas agendadas para el ${formatFecha(fecha) || 'esta fecha'}.</div>`;
            return;
        }
 
        lista.innerHTML = citas.map(c => {
            const yaAtendido = c.estado === 'completada';
            const horaFormato = formatearHora(c.hora_inicio);
            return `
            <div class="cita-card">
                <div class="cita-hora">${horaFormato}</div>
                <div class="cita-info">
                    <div class="paciente">👤 ${c.paciente}</div>
                    <div class="detalle">🏥 ${c.nombre_sala} &nbsp;|&nbsp; 📅 ${formatFecha(c.fecha)}</div>
                </div>
                <span class="badge ${yaAtendido ? 'badge-atendido' : 'badge-pendiente'}">
                    ${yaAtendido ? '✅ Atendido' : '⏳ Pendiente'}
                </span>
                <button class="btn-atender" onclick="marcarAtendido(${c.id_cita})" ${yaAtendido ? 'disabled' : ''}>
                    ${yaAtendido ? 'Listo' : 'Marcar atendido'}
                </button>
            </div>`;
        }).join('');
    })
    .catch(err => {
        console.error(err);
        lista.innerHTML = '<div class="empty-msg">❌ No se pudo conectar con el servidor.</div>';
    });
}
 
// ─── MARCAR CITA COMO ATENDIDA ───
 
function marcarAtendido(idCita) {
    fetch(`${API_URL}/citas/${idCita}/completar`, {
        method: 'PATCH',
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarToast('✅ Paciente marcado como atendido');
            renderAgenda();
        } else {
            mostrarToast('❌ ' + data.message);
        }
    })
    .catch(err => {
        console.error(err);
        mostrarToast('❌ Error al conectar con el servidor.');
    });
}
 
// ─── UTILIDAD: FORMATEAR HORA DE BD (HH:MM:SS → hh:MM AM/PM) ───
 
function formatearHora(horaStr) {
    if (!horaStr) return '';
    const [hh, mm] = horaStr.split(':').map(Number);
    const periodo = hh >= 12 ? 'PM' : 'AM';
    const h12 = hh % 12 || 12;
    return `${String(h12).padStart(2, '0')}:${String(mm).padStart(2, '0')} ${periodo}`;
}
 
function mostrarToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}
 
// ─── INICIALIZACIÓN ───
document.addEventListener('DOMContentLoaded', () => {
    mostrarPanel();
});
 
// ─── PESTAÑAS ───
 
function cambiarTab(tab) {
    document.getElementById('tab-dia').classList.toggle('active',   tab === 'dia');
    document.getElementById('tab-todas').classList.toggle('active', tab === 'todas');
    document.getElementById('panel-dia').style.display   = tab === 'dia'   ? 'block' : 'none';
    document.getElementById('panel-todas').style.display = tab === 'todas' ? 'block' : 'none';
 
    if (tab === 'todas') {
        filtrarTodas(''); // carga todas por defecto
    }
}
 
// ─── TODAS LAS CITAS ───
 
function filtrarTodas(estado) {
    // Actualizar botón activo
    ['todas', 'programada', 'completada', 'cancelada'].forEach(k => {
        const id = k === 'todas' ? 'f-todas' : `f-${k}`;
        document.getElementById(id).classList.toggle('active', 
            (estado === '' && k === 'todas') || estado === k
        );
    });
 
    const lista = document.getElementById('lista-todas');
    lista.innerHTML = '<div class="empty-msg">Consultando base de datos...</div>';
 
    const url = estado
        ? `${API_URL}/todas_citas?estado=${estado}`
        : `${API_URL}/todas_citas`;
 
    fetch(url, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        if (data.status !== 'success') {
            lista.innerHTML = `<div class="empty-msg">❌ Error: ${data.message}</div>`;
            return;
        }
 
        const citas = data.citas;
 
        if (citas.length === 0) {
            lista.innerHTML = '<div class="empty-msg">📭 No hay citas para este filtro.</div>';
            return;
        }
 
        lista.innerHTML = citas.map(c => {
            const yaAtendido = c.estado === 'completada';
            const cancelada  = c.estado === 'cancelada';
 
            let badgeClass = 'badge-programada';
            if (yaAtendido) badgeClass = 'badge-atendido';
            if (cancelada)  badgeClass = 'badge-cancelada';
 
            let badgeLabel = '⏳ Pendiente';
            if (yaAtendido) badgeLabel = '✅ Atendido';
            if (cancelada)  badgeLabel = '❌ Cancelada';
 
            return `
            <div class="cita-card">
                <div class="cita-hora">${formatearHora(c.hora_inicio)}</div>
                <div class="cita-info">
                    <div class="paciente">👤 ${c.paciente}</div>
                    <div class="detalle">
                        📅 ${formatFecha(c.fecha)}
                        &nbsp;|&nbsp;
                        🏥 ${c.nombre_sala}
                    </div>
                </div>
                <span class="badge ${badgeClass}">${badgeLabel}</span>
                <button class="btn-atender"
                    onclick="marcarAtendidoYRecargar(${c.id_cita}, '${estado}')"
                    ${yaAtendido || cancelada ? 'disabled' : ''}>
                    ${yaAtendido || cancelada ? 'Listo' : 'Marcar atendido'}
                </button>
            </div>`;
        }).join('');
    })
    .catch(err => {
        console.error(err);
        lista.innerHTML = '<div class="empty-msg">❌ No se pudo conectar con el servidor.</div>';
    });
}
 
// Marcar atendido desde la pestaña "Todas" y recargar con el filtro activo
function marcarAtendidoYRecargar(idCita, estadoActual) {
    fetch(`${API_URL}/citas/${idCita}/completar`, {
        method: 'PATCH',
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarToast('✅ Paciente marcado como atendido');
            filtrarTodas(estadoActual);
        } else {
            mostrarToast('❌ ' + data.message);
        }
    })
    .catch(() => mostrarToast('❌ Error al conectar con el servidor.'));
}