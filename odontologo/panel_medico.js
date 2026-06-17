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
 

// ─── CARGAR DATOS DEL PERFIL ───
function cargarPerfilDoctor() {
    fetch(`${API_URL}/perfil`, {
        method: 'GET',
        credentials: 'include' // Vital para que Python reconozca la sesión
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // Construimos el nombre con el formato "Dr. Nombre Apellido"
            const nombreCompleto = `Dr. ${data.perfil.nombre} ${data.perfil.apellido}`;
            
            // Inyectamos el nombre en los dos lugares del HTML
            document.getElementById('doctor-name-welcome').innerText = nombreCompleto;
            document.getElementById('doctor-name-agenda').innerText = nombreCompleto;
        } else {
            // SEGURIDAD: Si no hay sesión válida o no es rol odontólogo, lo devolvemos al login
            alert("Tu sesión ha expirado o no tienes acceso. Por favor, inicia sesión de nuevo.");
            window.location.href = '../login/login.html';
        }
    })
    .catch(err => {
        console.error("Error cargando perfil:", err);
        mostrarToast("❌ Error al cargar los datos del doctor");
    });
}


// ─── INICIALIZACIÓN ───
document.addEventListener('DOMContentLoaded', () => {
    cargarPerfilDoctor();
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

            // ── Bloque de motivo (solo si está cancelada y tiene motivo) ──
            const motivoHtml = (cancelada && c.motivo_cancelacion)
                ? `<div class="motivo-cancelacion">
                       <span class="motivo-label">💬 Motivo de cancelación:</span>
                       <span class="motivo-texto">${c.motivo_cancelacion}</span>
                   </div>`
                : '';

            return `
            <div class="cita-card ${cancelada ? 'cita-card-cancelada' : ''}">
                <div class="cita-hora">${formatearHora(c.hora_inicio)}</div>
                <div class="cita-info">
                    <div class="paciente">👤 ${c.paciente}</div>
                    <div class="detalle">
                        📅 ${formatFecha(c.fecha)}
                        &nbsp;|&nbsp;
                        🏥 ${c.nombre_sala}
                    </div>
                    ${motivoHtml}
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

// ─── CAMBIO DE MÓDULO ───
function irAModoPaciente() {
    // Redirecciona al panel de la agenda del cliente
    window.location.href = '../agenda_cliente/index.html';
}

// ─── CERRAR SESIÓN ABSOLUTO ───
function cerrarSesionMedico() {
    if (!confirm("¿Estás seguro de que deseas cerrar tu sesión actual en CLINIDENT?")) return;

    // Petición al servidor Flask para destruir de raíz las cookies de sesión
    fetch('/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Borrado exitoso, expulsamos al usuario directo a la pantalla de login
            // Ajusta los '../' según dónde se ubique exactamente tu login.html
            window.location.href = '../login/login.html';
        } else {
            mostrarToast("❌ No se pudo cerrar la sesión correctamente");
        }
    })
    .catch(err => {
        console.error("Error al cerrar sesión:", err);
        mostrarToast("❌ Error de conexión al cerrar sesión");
    });
}