
let pacientes      = [];
let indiceEliminar = null;
 
let chartEdadInstancia   = null;
let chartEstadoInstancia = null;
let chartFechaInstancia  = null;
 
const API_URL = '';

let filtroEstadoActivo = "todas";
let filtroFecha        = { modo: "dia", diaExacto: null, inicio: null, fin: null };
let tabFechaActiva     = "dia";
 
// --- INICIALIZADOR DE EVENTOS CUANDO CARGA EL DOM ---
document.addEventListener("DOMContentLoaded", () => {
    cargarCitasDesdeServidor();
 
    // Buscador
    const buscador = document.getElementById("buscador");
    if (buscador) buscador.addEventListener("input", mostrarPacientes);
 
    // Modales de eliminación
    const btnConfirmarEliminar = document.getElementById("btnConfirmarEliminar");
    if (btnConfirmarEliminar) btnConfirmarEliminar.addEventListener("click", confirmarEliminar);
 
    const btnCancelarEliminar = document.getElementById("btnCancelarEliminar");
    if (btnCancelarEliminar) btnCancelarEliminar.addEventListener("click", cerrarModalEliminar);
 
    // Exportaciones
    const btnExcel = document.getElementById("btnExcel");
    if (btnExcel) btnExcel.addEventListener("click", exportarExcel);
 
    const btnPDF = document.getElementById("btnPDF");
    if (btnPDF) btnPDF.addEventListener("click", exportarPDF);
 
    // --- DROPDOWN FILTRO POR ESTADO ---
    const btnFiltro    = document.getElementById("btnFiltroEstado");
    const dropdown     = document.getElementById("dropdownEstado");
    const labelFiltro  = document.getElementById("labelFiltroEstado");
    const dropdownFecha = document.getElementById("dropdownFecha");
 
    if (btnFiltro && dropdown) {
 
        btnFiltro.addEventListener("click", (e) => {
            e.stopPropagation();
            const estaAbierto = dropdown.style.display === "block";
            dropdown.style.display = estaAbierto ? "none" : "block";
            if (dropdownFecha) dropdownFecha.style.display = "none";
        });
 
        dropdown.addEventListener("click", (e) => e.stopPropagation());
 
        document.querySelectorAll(".opcion-estado").forEach(opcion => {
            opcion.addEventListener("click", () => {
                filtroEstadoActivo = opcion.dataset.valor;
 
                labelFiltro.textContent = opcion.textContent.trim();
                labelFiltro.style.color = opcion.style.color;
 
                document.querySelectorAll(".opcion-estado").forEach(o => o.classList.remove("activa-seleccion"));
                opcion.classList.add("activa-seleccion");
 
                dropdown.style.display = "none";
                mostrarPacientes();
            });
        });
    }
 
    // --- DROPDOWN FILTRO POR FECHA ---
    const btnFecha = document.getElementById("btnFiltroFecha");
 
    if (btnFecha && dropdownFecha) {
 
        btnFecha.addEventListener("click", (e) => {
            e.stopPropagation();
            const estaAbierto = dropdownFecha.style.display === "block";
            dropdownFecha.style.display = estaAbierto ? "none" : "block";
            if (dropdown) dropdown.style.display = "none";
        });
 
        dropdownFecha.addEventListener("click", (e) => e.stopPropagation());
    }
 
    // Cerrar ambos dropdowns al hacer clic fuera
    document.addEventListener("click", () => {
        if (dropdown)      dropdown.style.display      = "none";
        if (dropdownFecha) dropdownFecha.style.display = "none";
    });
});
 
// --- CONEXIÓN CON EL BACKEND (FLASK) ---
function cargarCitasDesdeServidor() {
    fetch(`${API_URL}/historial_citas/todas`, { credentials: 'include' })
        .then(res => {
            if (!res.ok) throw new Error("No autorizado o error de permisos");
            return res.json();
        })
        .then(data => {
            pacientes = data;
            actualizarDashboard();
        })
        .catch(err => {
            console.error("Error al cargar el historial desde SQLite:", err);
            mostrarNotificacion("Error al conectar con el servidor", "error");
        });
}
 
// --- CONTROL DE NAVEGACIÓN (SPA) ---
function cambiarSeccion(idSeccion) {
    document.querySelectorAll('.seccion').forEach(sec => sec.classList.remove('activa'));
    document.getElementById(idSeccion).classList.add('activa');
 
    if (idSeccion === 'seccion-dashboard')    actualizarDashboard();
    if (idSeccion === 'seccion-historial')    mostrarPacientes();
    if (idSeccion === 'seccion-estadisticas') dibujarGraficos();
}
 
function mostrarNotificacion(mensaje, tipo = "success") {
    const notif   = document.createElement("div");
    notif.textContent = mensaje;
    const esError = tipo === "error";
    notif.style.cssText = `
        position: fixed; top: 24px; left: 50%; transform: translateX(-50%);
        background: ${esError ? 'rgba(74,26,26,0.95)' : 'rgba(26,74,46,0.95)'};
        color: ${esError ? '#f87171' : '#4ade80'};
        border: 1px solid ${esError ? '#f87171' : '#4ade80'};
        padding: 14px 20px; border-radius: 8px; font-size: 14px;
        font-weight: bold; z-index: 9999; transition: opacity 0.5s;
    `;
    document.body.appendChild(notif);
    setTimeout(() => { notif.style.opacity = "0"; }, 2500);
    setTimeout(() => { notif.remove(); }, 3000);
}
 
// --- LÓGICA DEL DASHBOARD ---
function actualizarDashboard() {
    document.getElementById("totalPacientes").textContent = pacientes.length;
 
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById("totalHoy").textContent = pacientes.filter(p => p.fecha === hoy).length;
 
    const atendidos  = pacientes.filter(p => p.estado === "Atendido").length;
    const porcentaje = pacientes.length > 0 ? Math.round((atendidos / pacientes.length) * 100) : 0;
    document.getElementById("totalAsistencia").textContent = porcentaje + "%";
 
    const tbody = document.getElementById("listaPacientes");
    tbody.innerHTML = "";
 
    pacientes.slice(-5).reverse().forEach(p => {
        const estadoClase = p.estado === "Atendido" ? "badge-success" :
                            p.estado === "Pendiente" ? "badge-warning" : "badge-danger";
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td>${p.paciente}</td>
            <td>${p.fecha || "—"}</td>
            <td><span class="badge ${estadoClase}">${p.estado || "—"}</span></td>
        `;
        tbody.appendChild(fila);
    });
}
 
function getBadge(estado) {
    if (estado === "Atendido")    return `<span class="badge badge-success">Atendido</span>`;
    if (estado === "Pendiente")   return `<span class="badge badge-warning">Pendiente</span>`;
    if (estado === "Ausente")     return `<span class="badge badge-danger">Ausente</span>`;
    if (estado === "Programada")  return `<span class="badge" style="background:rgba(30,58,100,0.8);color:#60a5fa;">Programada</span>`;
    if (estado === "Completada")  return `<span class="badge badge-success">Completada</span>`;
    if (estado === "Cancelada")   return `<span class="badge badge-danger">Cancelada</span>`;
    if (estado === "Reprogramada") return `<span class="badge badge-warning">Reprogramada</span>`;
    if (estado === "No_asistio")  return `<span class="badge" style="background:rgba(80,40,10,0.8);color:#fb923c;">No asistió</span>`;
    return `<span class="badge badge-secondary">${estado || 'sin estado'}</span>`;
}
 
function getBadgePago(estado) {
    if (estado === "Pagado")  return `<span class="badge" style="background:rgba(20,60,30,0.8);color:#4ade80;">✅ Pagado</span>`;
    if (estado === "—")       return `<span class="badge" style="background:rgba(50,50,50,0.8);color:#888;">— </span>`;
    return `<span class="badge" style="background:rgba(80,60,10,0.8);color:#facc15;">⏳ Pendiente</span>`;
}
// --- LÓGICA DEL HISTORIAL Y TABLAS ---
function mostrarPacientes() {
    const busqueda = document.getElementById("buscador").value.toLowerCase();
    const tabla    = document.getElementById("tablaPacientes");
 
    tabla.innerHTML = `<tr><td colspan="7" style="color:#aaa; padding:20px;">Cargando historial desde el servidor...</td></tr>`;
 
    fetch(`${API_URL}/historial_citas/todas`, { credentials: 'include' })
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener los datos del servidor");
            return response.json();
        })
        .then(citas => {
            tabla.innerHTML = "";
 
            const filtrados = citas.filter(c => {
                const coincideTexto =
                    c.paciente.toLowerCase().includes(busqueda) ||
                    c.odontologo.toLowerCase().includes(busqueda) ||
                    (c.sala || "").toLowerCase().includes(busqueda);
 
                const coincideEstado =
                    filtroEstadoActivo === "todas" ||
                    (c.estado || "").toLowerCase() === filtroEstadoActivo.toLowerCase();
 
                let coincideFecha = true;
                if (filtroFecha.diaExacto) {
                    coincideFecha = c.fecha === filtroFecha.diaExacto;
                } else if (filtroFecha.inicio && filtroFecha.fin) {
                    coincideFecha = c.fecha >= filtroFecha.inicio && c.fecha <= filtroFecha.fin;
                }
 
                return coincideTexto && coincideEstado && coincideFecha;
            });
 
            if (filtrados.length === 0) {
                let msg = "No se encontraron citas en el historial.";
                if (filtroFecha.diaExacto) {
                    msg = `Sin citas para el <strong>${formatearFecha(filtroFecha.diaExacto)}</strong>.`;
                } else if (filtroFecha.inicio && filtroFecha.fin) {
                    msg = `Sin citas entre el <strong>${formatearFecha(filtroFecha.inicio)}</strong> y el <strong>${formatearFecha(filtroFecha.fin)}</strong>.`;
                } else if (filtroEstadoActivo !== "todas") {
                    msg = `No hay citas con estado <strong>${document.getElementById("labelFiltroEstado").textContent}</strong>.`;
                }
                tabla.innerHTML = `<tr><td colspan="8" style="color:#aaa; padding:20px; text-align:center;">${msg}</td></tr>`;
                return;
            }
 
            filtrados.forEach((c) => {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>${c.paciente}</td>
                    <td>${c.odontologo}</td>
                    <td>${c.sala || "—"}</td>
                    <td>${c.fecha}</td>
                    <td style="font-weight:bold; color:#4ade80;">${c.horario || "—"}</td>
                    <td>${c.servicio || "—"}</td>
                    <td>${getBadge(c.estado)}</td>
                    <td>${getBadgePago(c.estado_pago)}</td> 
                    
                `;
                tabla.appendChild(fila);
            });
        })
        .catch(err => {
            console.error(err);
            tabla.innerHTML = `<tr><td colspan="8" style="color:#f87171; padding:20px;">⚠️ Error al conectar con el servidor de citas.</td></tr>`;
        });
}
 
// --- DETALLE DE CITA ---
function verDetalleCita(idCita) {
    fetch(`${API_URL}/historial_citas/detalle/${idCita}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (data.status === "error") {
                alert("Error: " + data.message);
                return;
            }
            alert(`📋 DETALLE DE LA CITA #${data.id_cita}\n\n` +
                  `• Paciente: ${data.paciente}\n` +
                  `• Odontólogo: ${data.odontologo}\n` +
                  `• Sala asignada: ${data.sala}\n` +
                  `• Fecha: ${data.fecha}\n` +
                  `• Horario exacto: ${data.hora_inicio} hasta las ${data.hora_fin}\n` +
                  `• Estado actual: ${data.estado.toUpperCase()}`);
        })
        .catch(err => {
            console.error(err);
            alert("No se pudo conectar con el servidor para ver el detalle.");
        });
}
 
function cerrarModal() {
    document.getElementById("modalOverlay").style.display = "none";
}
 
// --- EXPORTACIONES ---
function exportarExcel() {
    const datos = pacientes.map(p => ({
        Paciente:   p.paciente,
        Odontólogo: p.odontologo || "—",
        Sala:       p.sala       || "—",
        Fecha:      p.fecha      || "—",
        Horario:    p.horario    || "—",
        Estado:     p.estado     || "—",
    }));
    const ws = XLSX.utils.json_to_sheet(datos);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Historial de Citas");
    XLSX.writeFile(wb, "historial_clinident.xlsx");
}
 
function exportarPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.text("Historial Clínico de Citas – Clinident", 14, 16);
    doc.autoTable({
        startY: 22,
        head: [["Paciente", "Odontólogo", "Sala", "Fecha", "Horario", "Estado"]],
        body: pacientes.map(p => [
            p.paciente,
            p.odontologo || "—",
            p.sala       || "—",
            p.fecha      || "—",
            p.horario    || "—",
            p.estado     || "—",
        ]),
        styles:     { fontSize: 9 },
        headStyles: { fillColor: [45, 140, 240] },
    });
    doc.save("historial_clinident.pdf");
}
 
// --- GRÁFICOS ESTADÍSTICOS ---
function dibujarGraficos() {
    const colores = {
        azul:    "rgba(45, 140, 240, 0.8)",
        verde:   "rgba(74, 222, 128, 0.8)",
        naranja: "rgba(250, 204, 21, 0.8)",
        rojo:    "rgba(248, 113, 113, 0.8)",
        morado:  "rgba(167, 139, 250, 0.8)",
    };

    const opcionesBase = {
        responsive: true,
        plugins: { legend: { labels: { color: "white" } } },
        scales: {
            x: { ticks: { color: "white" }, grid: { color: "rgba(255,255,255,0.1)" } },
            y: { ticks: { color: "white" }, grid: { color: "rgba(255,255,255,0.1)" }, beginAtZero: true }
        }
    };

    if (chartEdadInstancia)   chartEdadInstancia.destroy();
    if (chartEstadoInstancia) chartEstadoInstancia.destroy();
    if (chartFechaInstancia)  chartFechaInstancia.destroy();

    // --- Gráfico de Salas ---
    const conteoSala = {};
    pacientes.forEach(p => { conteoSala[p.sala] = (conteoSala[p.sala] || 0) + 1; });

    chartEdadInstancia = new Chart(document.getElementById("graficoEdad"), {
        type: "bar",
        data: {
            labels: Object.keys(conteoSala),
            datasets: [{ label: "Citas por Sala", data: Object.values(conteoSala), backgroundColor: [colores.azul, colores.morado, colores.verde], borderWidth: 0, borderRadius: 6 }]
        },
        options: opcionesBase
    });

    // --- Gráfico de Estado (CORREGIDO) ---
    // Normalizar: contar dinámicamente todos los estados que lleguen desde la BD
    const conteoEstado = {};
    pacientes.forEach(p => {
        const estado = p.estado || "sin estado";
        conteoEstado[estado] = (conteoEstado[estado] || 0) + 1;
    });

    // Filtrar estados con al menos 1 cita para no mostrar segmentos vacíos
    const estadosConDatos = Object.entries(conteoEstado).filter(([, v]) => v > 0);
    const labelsEstado = estadosConDatos.map(([k]) => k);
    const valoresEstado = estadosConDatos.map(([, v]) => v);

    // Paleta de colores por nombre de estado (con fallback)
    const colorPorEstado = {
        "atendido":     colores.verde,
        "pendiente":    colores.naranja,
        "ausente":      colores.rojo,
        "programada":   colores.azul,
        "completada":   colores.verde,
        "cancelada":    colores.rojo,
        "reprogramada": colores.naranja,
        "no_asistio":   colores.morado,
        "sin estado":   "rgba(150,150,150,0.7)",
    };
    const bgEstado = labelsEstado.map(l => {
        const estadoNormalizado = l.trim().toLowerCase();
        return colorPorEstado[estadoNormalizado] || colores.azul;
    });

    chartEstadoInstancia = new Chart(document.getElementById("graficoEstado"), {
        type: "doughnut",
        data: {
            labels: labelsEstado,
            datasets: [{ data: valoresEstado, backgroundColor: bgEstado, borderWidth: 0 }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: "white" } },
                // Mostrar mensaje si no hay datos
                title: {
                    display: valoresEstado.length === 0,
                    text: "Sin datos disponibles",
                    color: "#aaa",
                    font: { size: 14 }
                }
            }
        }
    });

    // --- Gráfico de Flujo por Fecha ---
    const porFecha = {};
    pacientes.forEach(p => { const f = p.fecha || "Sin fecha"; porFecha[f] = (porFecha[f] || 0) + 1; });
    const fechasOrdenadas = Object.keys(porFecha).sort();

    chartFechaInstancia = new Chart(document.getElementById("graficoFecha"), {
        type: "line",
        data: {
            labels: fechasOrdenadas,
            datasets: [{ label: "Flujo de Citas", data: fechasOrdenadas.map(f => porFecha[f]), borderColor: colores.azul, backgroundColor: "rgba(45,140,240,0.15)", borderWidth: 2, pointBackgroundColor: colores.azul, fill: true, tension: 0.4 }]
        },
        options: opcionesBase
    });
}
 
// --- FILTRO POR FECHA ---
function cambiarTabFecha(tab) {
    tabFechaActiva = tab;
 
    document.getElementById("panelDia").style.display   = tab === "dia"   ? "block" : "none";
    document.getElementById("panelRango").style.display = tab === "rango" ? "block" : "none";
 
    document.getElementById("tabDia").style.background   = tab === "dia"   ? "#2D8CF0" : "rgba(52,53,56,0.8)";
    document.getElementById("tabDia").style.color        = tab === "dia"   ? "white"   : "#aaa";
    document.getElementById("tabRango").style.background = tab === "rango" ? "#2D8CF0" : "rgba(52,53,56,0.8)";
    document.getElementById("tabRango").style.color      = tab === "rango" ? "white"   : "#aaa";
}
 
function aplicarFiltroFecha() {
    const dropdownF = document.getElementById("dropdownFecha");
    const label     = document.getElementById("labelFiltroFecha");
 
    if (tabFechaActiva === "dia") {
        const dia = document.getElementById("inputDiaExacto").value;
        if (!dia) return;
        filtroFecha = { modo: "dia", diaExacto: dia, inicio: null, fin: null };
        label.textContent = formatearFecha(dia);
        label.style.color = "#60a5fa";
    } else {
        const inicio = document.getElementById("inputFechaInicio").value;
        const fin    = document.getElementById("inputFechaFin").value;
        if (!inicio || !fin) return;
        if (inicio > fin) {
            mostrarNotificacion("La fecha inicio no puede ser mayor que la fecha fin", "error");
            return;
        }
        filtroFecha = { modo: "rango", diaExacto: null, inicio, fin };
        label.textContent = `${formatearFecha(inicio)} → ${formatearFecha(fin)}`;
        label.style.color = "#60a5fa";
    }
 
    dropdownF.style.display = "none";
    mostrarPacientes();
}
 
function limpiarFiltroFecha() {
    filtroFecha = { modo: "dia", diaExacto: null, inicio: null, fin: null };
 
    document.getElementById("inputDiaExacto").value        = "";
    document.getElementById("inputFechaInicio").value      = "";
    document.getElementById("inputFechaFin").value         = "";
    document.getElementById("labelFiltroFecha").textContent = "Todas las fechas";
    document.getElementById("labelFiltroFecha").style.color = "white";
    document.getElementById("dropdownFecha").style.display  = "none";
 
    mostrarPacientes();
}
 
function formatearFecha(fechaISO) {
    const [y, m, d] = fechaISO.split("-");
    return `${d}/${m}/${y}`;
}
 
// --- COMPATIBILIDAD MODAL BORRADO ---
function cerrarModalEliminar() {}
function confirmarEliminar()   {}
 