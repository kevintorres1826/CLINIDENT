// --- VARIABLES GLOBALES DEL SISTEMA ---
let pacientes = []; // Ahora se llenará con las citas reales desde la Base de Datos
let indiceEliminar = null;

// Instancias globales para los gráficos de Chart.js
let chartEdadInstancia = null;
let chartEstadoInstancia = null;
let chartFechaInstancia = null;

// URL Base del servidor Flask (Ajustar si usas otro puerto)
const API_URL = 'http://127.0.0.1:5000';

// --- INICIALIZADOR DE EVENTOS CUANDO CARGA EL DOM ---
document.addEventListener("DOMContentLoaded", () => {
    // Cargamos los datos reales del servidor inmediatamente al abrir el módulo
    cargarCitasDesdeServidor();

    // Escucha para el buscador del historial
    const buscador = document.getElementById("buscador");
    if (buscador) {
        buscador.addEventListener("input", mostrarPacientes);
    }

    // Escuchas para los botones del modal de eliminación (Si decides usarlos con Flask)
    const btnConfirmarEliminar = document.getElementById("btnConfirmarEliminar");
    if (btnConfirmarEliminar) btnConfirmarEliminar.addEventListener("click", confirmarEliminar);

    const btnCancelarEliminar = document.getElementById("btnCancelarEliminar");
    if (btnCancelarEliminar) btnCancelarEliminar.addEventListener("click", cerrarModalEliminar);

    // Escuchas para los botones de exportación
    const btnExcel = document.getElementById("btnExcel");
    if (btnExcel) btnExcel.addEventListener("click", exportarExcel);

    const btnPDF = document.getElementById("btnPDF");
    if (btnPDF) btnPDF.addEventListener("click", exportarPDF);
});

// --- CONEXIÓN CON EL BACKEND (FLASK) ---
function cargarCitasDesdeServidor() {
    fetch(`${API_URL}/historial_citas/todas`)
        .then(res => {
            if (!res.ok) throw new Error("No autorizado o error de permisos");
            return res.json();
        })
        .then(data => {
            pacientes = data; // Guardamos el array de citas devuelto por Python
            // Actualizamos la vista inicial del Dashboard
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
    
    if (idSeccion === 'seccion-dashboard') actualizarDashboard();
    if (idSeccion === 'seccion-historial') mostrarPacientes();
    if (idSeccion === 'seccion-estadisticas') dibujarGraficos();
}

function mostrarNotificacion(mensaje, tipo = "success") {
    const notif = document.createElement("div");
    notif.textContent = mensaje;
    
    const esError = tipo === "error";
    notif.style.cssText = `
        position: fixed;
        top: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: ${esError ? 'rgba(74,26,26,0.95)' : 'rgba(26,74,46,0.95)'};
        color: ${esError ? '#f87171' : '#4ade80'};
        border: 1px solid ${esError ? '#f87171' : '#4ade80'};
        padding: 14px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        z-index: 9999;
        transition: opacity 0.5s;
    `;
    document.body.appendChild(notif);
    setTimeout(() => { notif.style.opacity = "0"; }, 2500);
    setTimeout(() => { notif.remove(); }, 3000);
}

// --- LÓGICA DEL DASHBOARD ---
function actualizarDashboard() {
    document.getElementById("totalPacientes").textContent = pacientes.length;

    // Formato de fecha del servidor local (YYYY-MM-DD)
    const hoy = new Date().toISOString().split('T')[0];
    const registradosHoy = pacientes.filter(p => p.fecha === hoy);
    document.getElementById("totalHoy").textContent = registradosHoy.length;

    const atendidos = pacientes.filter(p => p.estado === "Atendido").length;
    const porcentaje = pacientes.length > 0 ? Math.round((atendidos / pacientes.length) * 100) : 0;
    document.getElementById("totalAsistencia").textContent = porcentaje + "%";

    const tbody = document.getElementById("listaPacientes");
    tbody.innerHTML = "";
    
    // Muestra las últimas 5 citas reales mapeadas de la BD
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
    if (estado === "Atendido") return `<span class="badge badge-success">Atendido</span>`;
    if (estado === "Pendiente") return `<span class="badge badge-warning">Pendiente</span>`;
    if (estado === "Ausente")   return `<span class="badge badge-danger">Ausente</span>`;
    return `<span class="badge badge-secondary">${estado || 'sin estado'}</span>`;
}

// --- LÓGICA DEL HISTORIAL Y TABLAS ---
function mostrarPacientes() {
    const busqueda = document.getElementById("buscador").value.toLowerCase();
    const tabla = document.getElementById("tablaPacientes");
    
    // Indicador visual de carga
    tabla.innerHTML = `<tr><td colspan="8" style="color:#aaa; padding:20px;">Cargando historial desde el servidor...</td></tr>`;

    // Conexión real al endpoint de Flask que creamos
    fetch('/historial_citas/todas')
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener los datos del servidor");
            return response.json();
        })
        .then(citas => {
            tabla.innerHTML = "";

            // Filtramos las citas por nombre de paciente, odontólogo o sala
            const filtrados = citas.filter(c =>
                c.paciente.toLowerCase().includes(busqueda) ||
                c.odontologo.toLowerCase().includes(busqueda) ||
                (c.sala || "").toLowerCase().includes(busqueda)
            );

            if (filtrados.length === 0) {
                tabla.innerHTML = `<tr><td colspan="8" style="color:#aaa; padding:20px;">No se encontraron citas en el historial.</td></tr>`;
                return;
            }

            // Iteramos sobre las citas de la Base de Datos SQLite
            filtrados.forEach((c) => {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>${c.paciente}</td>
                    <td>${c.odontologo}</td>
                    <td>${c.sala || "—"}</td>
                    <td>${c.fecha}</td>
                    <td style="font-weight: bold; color: #4ade80;">${c.horario || "—"}</td>
                    <td>${c.servicio || "—"}</td>
                    <td>${getBadge(c.estado)}</td>
                    <td>
                        <button class="btn-editar" onclick="verDetalleCita(${c.id_cita})" style="padding: 5px 10px; font-size: 12px;">👁️ Ver Detalle</button>
                    </td>
                `;
                tabla.appendChild(fila);
            });
        })
        .catch(err => {
            console.error(err);
            tabla.innerHTML = `<tr><td colspan="7" style="color:#f87171; padding:20px;">⚠️ Error al conectar con el servidor de citas.</td></tr>`;
        });
}

// --- CONTROL DE DETALLE (Vinculado al endpoint dinámico de Flask) ---
function verDetalleCita(idCita) {
    fetch(`${API_URL}/historial_citas/detalle/${idCita}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === "error") {
                mostrarNotificacion(data.message, "error");
                return;
            }
            
            // Aquí puedes inyectar las propiedades reales del JSON (historial_clinico, factura, etc.)
            // en un modal contenedor de tu HTML para visualizar la información médica completa.
            console.log("Datos de la cita cargados:", data);
            
            alert(`Detalle Clínico de ${data.paciente}:\n` +
                  `Odontólogo: ${data.odontologo}\n` +
                  `Sala: ${data.sala}\n` +
                  `Estado: ${data.estado_descripcion}\n` +
                  `Monto Factura: ${data.factura ? '$' + data.factura.monto : 'Sin facturar'}`);
        })
        .catch(err => console.error("Error al obtener detalle:", err));
}

function cerrarModal() {
    document.getElementById("modalOverlay").style.display = "none";
}

// --- EXPORTACIONES ---
function exportarExcel() {
    const datos = pacientes.map(p => ({
        Paciente:    p.paciente,
        Odontólogo:  p.odontologo || "—",
        Sala:        p.sala || "—",
        Fecha:       p.fecha || "—",
        Horario:     `${p.hora_inicio} - ${p.hora_fin}`,
        Estado:      p.estado || "—",
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
            p.sala || "—",
            p.fecha || "—",
            `${p.hora_inicio} - ${p.hora_fin}`,
            p.estado || "—",
        ]),
        styles: { fontSize: 9 },
        headStyles: { fillColor: [45, 140, 240] },
    });
    doc.save("historial_clinident.pdf");
}

// --- GRÁFICOS ESTADÍSTICOS CON DATOS REALES ---
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

    if (chartEdadInstancia) chartEdadInstancia.destroy();
    if (chartEstadoInstancia) chartEstadoInstancia.destroy();
    if (chartFechaInstancia) chartFechaInstancia.destroy();

    // Gráfico 1 — Mapeado por Sala en vez de edad (La BD de citas no trae edad en la lista general)
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

    // Gráfico 2 — Estado de la Cita (Real)
    const conteoEstado = { Atendido: 0, Pendiente: 0, Ausente: 0 };
    pacientes.forEach(p => { 
        if (conteoEstado[p.estado] !== undefined) conteoEstado[p.estado]++; 
    });
    
    chartEstadoInstancia = new Chart(document.getElementById("graficoEstado"), {
        type: "doughnut",
        data: {
            labels: ["Atendido", "Pendiente", "Ausente"],
            datasets: [{ data: [conteoEstado.Atendido, conteoEstado.Pendiente, conteoEstado.Ausente], backgroundColor: [colores.verde, colores.naranja, colores.rojo], borderWidth: 0 }]
        },
        options: { responsive: true, plugins: { legend: { labels: { color: "white" } } } }
    });

    // Gráfico 3 — Volumen por fechas
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

// Funciones vacías por compatibilidad de botones del modal de borrado
function cerrarModalEliminar() {}
function confirmarEliminar() {}

function verDetalleCita(idCita) {
    fetch(`/historial_citas/detalle/${idCita}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === "error") {
                alert("Error: " + data.message);
                return;
            }
            // Alerta informativa limpia para validar que los datos llegan correctamente
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