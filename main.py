import socket  # Librería nativa para verificar la disponibilidad de puerto
from flask import Flask, send_from_directory, session, jsonify, redirect
from flask_cors import CORS
from datetime import timedelta
import os
import sys
import sqlite3  # Librería nativa para interactuar con SQLite

# 1. IMPORTAR COMPONENTES
from login.login import login_blueprint
from login.recuperacion import recuperacion_blueprint
from login.registro import registro_blueprint           
from agenda_cliente.agenda_cliente import agenda_blueprint 
from odontologo.odontologo import odontologo_blueprint 
from recepcionista.agenda_recepcion import agenda_recepcion_blueprint

app = Flask(__name__)

# OBTENER LA RUTA REAL DONDE SE EJECUTA EL .EXE O EL SCRIPT
if getattr(sys, 'frozen', False):
    # 1. ruta_exe: Donde el usuario puso el .exe (Ej: Escritorio). Útil para la BD.
    ruta_exe = os.path.dirname(sys.executable)
    
    # 2. ruta_frontend: La carpeta temporal donde PyInstaller esconde tus HTML/CSS
    ruta_frontend = sys._MEIPASS 
else:
    # Modo desarrollo normal
    ruta_exe = os.path.dirname(os.path.abspath(__file__))
    ruta_frontend = ruta_exe

# La base de datos SIEMPRE se guarda afuera, usando ruta_exe
RUTA_BD = os.path.join(ruta_exe, "clinident.db")
# 🚀 FUNCIÓN DE AUTOREPARACIÓN DE BASE DE DATOS COMPLETA
def inicializar_base_de_datos():
    """ 
    Si clinident.db no existe en la carpeta raíz del proyecto, 
    la crea automáticamente con todas las tablas y registros originales.
    """
    if not os.path.exists(RUTA_BD):
        print("\n⚠️ No se encontró 'clinident.db' en la raíz.")
        print("🔨 Iniciando construcción automática de la base de datos portátil con tus registros...")
        
        sql_script = """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS `tblrol` (
          `id_rol` INTEGER PRIMARY KEY AUTOINCREMENT,
          `rol` varchar(50) NOT NULL UNIQUE,
          `descripcion` text NOT NULL
        );

        INSERT OR IGNORE INTO `tblrol` (`id_rol`, `rol`, `descripcion`) VALUES
        (1, 'administrador', 'Acceso total al sistema: usuarios, reportes y configuración'),
        (2, 'odontologo', 'Acceso a agenda, tratamientos, historial clínico y registros'),
        (3, 'recepcionista', 'Acceso a agenda, programar y modificar citas'),
        (4, 'paciente', 'Acceso de solo lectura a sus propias citas e historial');

        CREATE TABLE IF NOT EXISTS `tblusuario` (
          `id_usuario` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_rol` int(11) NOT NULL,
          `nombre` varchar(80) NOT NULL,
          `apellido` varchar(80) NOT NULL,
          `correo` varchar(120) NOT NULL UNIQUE,
          `telefono` varchar(20) DEFAULT NULL,
          `contrasena` varchar(255) NOT NULL,
          `estado` varchar(10) NOT NULL DEFAULT 'Activo',
          FOREIGN KEY (`id_rol`) REFERENCES `tblrol` (`id_rol`) ON UPDATE CASCADE
        );

        INSERT OR IGNORE INTO `tblusuario` (`id_usuario`, `id_rol`, `nombre`, `apellido`, `correo`, `telefono`, `contrasena`, `estado`) VALUES
        (1, 1, 'Simon', 'rodriguez', 'simonbol@gmail.com', '3113102302', 'lagranclombia3', 'Activo'),
        (2, 1, 'William', 'Afton', 'jajapt@gmail.com', '3202274907', 'IIItenchingue', 'Activo'),
        (3, 2, 'William', 'Alton', 'WilliA@gmail.com', '3001665297', 'Willy-notall_000', 'Activo'),
        (4, 2, 'Michael', 'Phillips', 'phillipsmike@soy.sera.edu.co', '3202224807', 'GrandTheftAuto_175', 'Activo'),
        (5, 2, 'Alberto', 'Fernandez', 'Albertofernandez@gmail.com', '3503476575', 'Charlieadaasuelo_908', 'Activo'),
        (6, 3, 'Robert', 'Patinson', 'patinsonRobert@gmail.com', '3272477253', 'RobertPatinson233', 'Activo'),
        (7, 3, 'Sean', 'Combs', 'saunCo@gmail.com', '3048702856', 'Piddlynuse_702', 'Activo'),
        (8, 4, 'Juan', 'Hernandez', 'juanhernavez2@gmail.com', '3203989375', 'focaNocsa02_+', 'Activo'),
        (101, 4, 'Juan', 'Cortes', 'juan.D.uvioo@gmail.com', '3006567890', 'TempPass101', 'Activo'),
        (102, 4, 'Ana', 'Gomez', 'ana.gomez2@notmail.com', '3175578901', 'TempPass102', 'Activo'),
        (103, 4, 'Luis', 'Torres', 'luis.forres@gmail.com', '3206788012', 'TempPass103', 'Activo'),
        (104, 4, 'Maria', 'Lopez', 'maria.lopez@gmail.com', '3197090723', 'TempPass104', 'Activo'),
        (105, 4, 'Camila', 'Suarez', 'camila.suiz@gmail.com', '3008013234', 'TempPass105', 'Activo'),
        (106, 4, 'David', 'Martinez', 'david.martinez@gmail.com', '3098012345', 'TempPass106', 'Activo'),
        (107, 4, 'Sofia', 'Hernandez', 'sofia.herncruz@gmail.com', '3102123456', 'TempPass107', 'Activo'),
        (108, 4, 'Carlos', 'Diaz', 'carlos.diaz@yahoo.com', '3442778421', 'TempPass108', 'Activo'),
        (109, 4, 'Valeria', 'Moreno', 'valeria.moreno@gmail.com', '2002999824', 'TempPass109', 'Activo'),
        (110, 4, 'Nicolas', 'Vargas', 'nicolas.vargas@gmail.com', '3503885587', 'TempPass110', 'Activo');

        CREATE TABLE IF NOT EXISTS `tblsala` (
          `id_sala` INTEGER PRIMARY KEY AUTOINCREMENT,
          `nombre_sala` varchar(80) NOT NULL UNIQUE,
          `disponibilidad` tinyint(1) NOT NULL DEFAULT 1
        );

        INSERT OR IGNORE INTO `tblsala` (`id_sala`, `nombre_sala`, `disponibilidad`) VALUES
        (1, 'Rayos X', 1),
        (2, 'Consultorio 1', 1),
        (3, 'Consultorio 2', 1),
        (4, 'Cirugía', 1),
        (5, 'Limpieza', 1);

        CREATE TABLE IF NOT EXISTS `tblcita` (
          `id_cita` INTEGER PRIMARY KEY AUTOINCREMENT,
          `fecha` date NOT NULL,
          `hora_inicio` time NOT NULL,
          `hora_fin` time NOT NULL,
          `id_usuario` int(11) DEFAULT NULL,
          `id_odontologo` int(11) NOT NULL,
          `id_sala` int(11) NOT NULL,
          FOREIGN KEY (`id_odontologo`) REFERENCES `tblusuario` (`id_usuario`) ON UPDATE CASCADE,
          FOREIGN KEY (`id_sala`) REFERENCES `tblsala` (`id_sala`) ON UPDATE CASCADE,
          FOREIGN KEY (`id_usuario`) REFERENCES `tblusuario` (`id_usuario`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_cita_paciente` ON `tblcita` (`id_usuario`);
        CREATE INDEX IF NOT EXISTS `idx_cita_odontologo` ON `tblcita` (`id_odontologo`);
        CREATE INDEX IF NOT EXISTS `idx_cita_fecha` ON `tblcita` (`fecha`);

        INSERT OR IGNORE INTO `tblcita` (`id_cita`, `fecha`, `hora_inicio`, `hora_fin`, `id_usuario`, `id_odontologo`, `id_sala`) VALUES
        (201, '2026-03-10', '08:00:00', '09:30:00', 101, 3, 2),
        (202, '2026-03-10', '11:00:00', '12:30:00', 102, 4, 2),
        (203, '2026-03-10', '10:30:00', '11:30:00', 103, 3, 3),
        (204, '2026-03-10', '09:00:00', '09:30:00', 104, 4, 2),
        (205, '2026-03-11', '08:00:00', '09:30:00', 103, 3, 4),
        (206, '2026-03-11', '09:00:00', '09:30:00', 105, 4, 2),
        (207, '2026-03-12', '08:00:00', '10:30:00', 106, 3, 4),
        (208, '2026-03-11', '11:00:00', '11:30:00', 106, 5, 5),
        (209, '2026-03-11', '10:00:00', '10:30:00', 107, 4, 2),
        (210, '2026-03-12', '08:00:00', '09:30:00', 108, 3, 4);

        CREATE TABLE IF NOT EXISTS `tblestadocita` (
          `id_estado` INTEGER PRIMARY KEY AUTOINCREMENT,
          `nombre_estado` varchar(30) NOT NULL UNIQUE,
          `descripcion` varchar(150) DEFAULT NULL
        );

        INSERT OR IGNORE INTO `tblestadocita` (`id_estado`, `nombre_estado`, `descripcion`) VALUES
        (1, 'programada', 'Cita agendada y confirmada'),
        (2, 'cancelada', 'Cita cancelada por el paciente o la clínica'),
        (3, 'reprogramada', 'Cita movida a nueva fecha u hora'),
        (4, 'completada', 'Cita realizada exitosamente'),
        (5, 'no_asistio', 'El paciente no se presentó');

        CREATE TABLE IF NOT EXISTS `tblagenda` (
          `id_cita` int(11) NOT NULL PRIMARY KEY,
          `id_estado` int(11) NOT NULL,
          FOREIGN KEY (`id_cita`) REFERENCES `tblcita` (`id_cita`) ON DELETE CASCADE ON UPDATE CASCADE,
          FOREIGN KEY (`id_estado`) REFERENCES `tblestadocita` (`id_estado`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_agencia_estado` ON `tblagenda` (`id_estado`);

        INSERT OR IGNORE INTO `tblagenda` (`id_cita`, `id_estado`) VALUES
        (201, 1), (203, 1), (205, 1), (206, 1), (207, 1), (208, 1), (209, 1), (202, 2), (210, 2), (204, 3);

        CREATE TABLE IF NOT EXISTS `tblversionley` (
          `version` varchar(10) NOT NULL PRIMARY KEY,
          `texto_legal` varchar(200) NOT NULL,
          `fecha_vigencia` date NOT NULL
        );

        INSERT OR IGNORE INTO `tblversionley` (`version`, `texto_legal`, `fecha_vigencia`) VALUES
        ('v1.0', 'Términos y condiciones de tratamiento v1.0', '2026-01-01');

        CREATE TABLE IF NOT EXISTS `tblconsentimiento` (
          `id_consentimiento` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_usuario` int(11) NOT NULL,
          `version` varchar(10) NOT NULL,
          `firma` tinyint(1) NOT NULL DEFAULT 0,
          `fecha` date NOT NULL,
          FOREIGN KEY (`id_usuario`) REFERENCES `tblusuario` (`id_usuario`) ON UPDATE CASCADE,
          FOREIGN KEY (`version`) REFERENCES `tblversionley` (`version`) ON UPDATE CASCADE
        );

        INSERT OR IGNORE INTO `tblconsentimiento` (`id_consentimiento`, `id_usuario`, `version`, `firma`, `fecha`) VALUES
        (1, 1, 'v1.0', 1, '2026-01-05'),
        (2, 8, 'v1.0', 1, '2026-01-08'),
        (3, 2, 'v1.0', 0, '2026-01-10'),
        (4, 4, 'v1.0', 1, '2026-01-13'),
        (5, 5, 'v1.0', 0, '2026-01-15');

        CREATE TABLE IF NOT EXISTS `tbltipotratamiento` (
          `id_tipo` INTEGER PRIMARY KEY AUTOINCREMENT,
          `nombre` varchar(80) NOT NULL UNIQUE,
          `descripcion` text DEFAULT NULL
        );

        INSERT OR IGNORE INTO `tbltipotratamiento` (`id_tipo`, `nombre`, `descripcion`) VALUES
        (1, 'Limpieza dental', 'Profilaxis y remoción de sarro y placa bacteriana'),
        (2, 'Ortodoncia', 'Corrección de posición dental mediante brackets o alineadores'),
        (3, 'Endodoncia', 'Tratamiento de conducto radicular'),
        (4, 'Blanqueamiento', 'Aclaramiento del esmalte dental'),
        (5, 'Extracción', 'Remoción de diente o muela'),
        (6, 'Implante dental', 'Implante de titanio con corona cerámica'),
        (7, 'Resina', 'Restauración estética con resina compuesta'),
        (8, 'Sellantes', 'Aplicación de sellantes de fisuras para prevención'),
        (9, 'Prótesis', 'Diseño y colocación de prótesis dental removible o fija'),
        (10, 'Cirugía oral', 'Extracción de muela del juicio u otras cirugías orales');

        CREATE TABLE IF NOT EXISTS `tbltratamiento` (
          `id_tratamiento` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_tipo` int(11) NOT NULL,
          `diagnostico` text NOT NULL,
          `valor` decimal(12,2) NOT NULL,
          `id_odontologo` int(11) NOT NULL,
          `id_usuario` int(11) DEFAULT NULL,
          FOREIGN KEY (`id_odontologo`) REFERENCES `tblusuario` (`id_usuario`) ON UPDATE CASCADE,
          FOREIGN KEY (`id_tipo`) REFERENCES `tbltipotratamiento` (`id_tipo`) ON UPDATE CASCADE,
          FOREIGN KEY (`id_usuario`) REFERENCES `tblusuario` (`id_usuario`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_trat_tipo` ON `tbltratamiento` (`id_tipo`);
        CREATE INDEX IF NOT EXISTS `idx_trat_paciente` ON `tbltratamiento` (`id_usuario`);
        CREATE INDEX IF NOT EXISTS `idx_trat_odontologo` ON `tbltratamiento` (`id_odontologo`);

        INSERT OR IGNORE INTO `tbltratamiento` (`id_tratamiento`, `id_tipo`, `diagnostico`, `valor`, `id_odontologo`, `id_usuario`) VALUES
        (301, 1, 'Placa bacteriana hallada en el procedimiento', 180000.00, 3, 101),
        (302, 2, 'Maloclusión hallada en el procedimiento', 2200000.00, 3, 107),
        (303, 3, 'Canal profunda tratada en el procedimiento', 720000.00, 4, 102),
        (304, 4, 'Manchas dentales', 830000.00, 5, 104),
        (305, 5, 'Se realizó la extracción de un diente fracturado', 700000.00, 5, 105),
        (306, 6, 'Caso profundo: implante dental de un paciente que pierde un diente', 2700000.00, 5, 108),
        (307, 7, 'Hallada una Caries leve', 350000.00, 4, 107),
        (308, 8, 'Se inicia programa de prevención correspondiente', 350000.00, 3, 103),
        (309, 9, 'Se hizo el implante dental de un paciente en sus dientes', 3800000.00, 6, 109),
        (310, 10, 'Se realiza la extracción de una muela del juicio de otra', 1600000.00, 5, 110);

        CREATE TABLE IF NOT EXISTS `tblfactura` (
          `id_factura` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_tratamiento` int(11) NOT NULL,
          `fecha_emision` date NOT NULL DEFAULT CURRENT_DATE,
          FOREIGN KEY (`id_tratamiento`) REFERENCES `tbltratamiento` (`id_tratamiento`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_factura_trat` ON `tblfactura` (`id_tratamiento`);

        INSERT OR IGNORE INTO `tblfactura` (`id_factura`, `id_tratamiento`, `fecha_emision`) VALUES
        (401, 301, '2026-02-05'), (402, 302, '2026-02-12'), (403, 303, '2026-02-20'), (404, 304, '2026-03-03'), (405, 305, '2026-03-10'), (406, 306, '2026-03-18'), (407, 307, '2026-03-23'), (408, 308, '2026-04-02'), (409, 309, '2026-04-10'), (410, 310, '2026-04-18');

        CREATE TABLE IF NOT EXISTS `tblhistorialclinico` (
          `id_historial_clinico` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_tratamiento` int(11) NOT NULL,
          `id_cita` int(11) NOT NULL,
          `observaciones` text DEFAULT NULL,
          `fecha` date NOT NULL,
          FOREIGN KEY (`id_cita`) REFERENCES `tblcita` (`id_cita`) ON UPDATE CASCADE,
          FOREIGN KEY (`id_tratamiento`) REFERENCES `tbltratamiento` (`id_tratamiento`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_hc_cita` ON `tblhistorialclinico` (`id_cita`);
        CREATE INDEX IF NOT EXISTS `idx_hc_tratamiento` ON `tblhistorialclinico` (`id_tratamiento`);

        INSERT OR IGNORE INTO `tblhistorialclinico` (`id_historial_clinico`, `id_tratamiento`, `id_cita`, `observaciones`, `fecha`) VALUES
        (701, 301, 201, 'Se recomienda limpieza cada 6 meses', '2026-02-05'),
        (702, 302, 202, 'Inicia tratamiento de ortodoncia', '2026-02-12'),
        (703, 303, 203, 'Requiere atención de endodoncia urgente', '2026-02-20'),
        (704, 304, 204, 'Seguimiento histórico estabilizado', '2026-03-03'),
        (705, 305, 205, 'Extracción sin complicaciones', '2026-03-10'),
        (706, 306, 206, 'Se programa implante', '2026-03-18'),
        (707, 307, 207, 'Aplicación de resina', '2026-03-23'),
        (708, 308, 208, 'Aplicación de sellantes', '2026-04-02'),
        (709, 309, 209, 'Se toma molde para prótesis', '2026-04-10'),
        (710, 310, 210, 'Cirugía exitosa', '2026-04-18');

        CREATE TABLE IF NOT EXISTS `tblhistorialfacturacion` (
          `id_historial` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_factura` int(11) NOT NULL,
          `fecha_emision` date NOT NULL,
          FOREIGN KEY (`id_factura`) REFERENCES `tblfactura` (`id_factura`) ON DELETE CASCADE ON UPDATE CASCADE
        );

        INSERT OR IGNORE INTO `tblhistorialfacturacion` (`id_historial`, `id_factura`, `fecha_emision`) VALUES
        (1, 401, '2026-02-05'), (2, 402, '2026-02-12'), (3, 403, '2026-02-20'), (4, 404, '2026-03-03'), (5, 405, '2026-03-10'), (6, 406, '2026-03-18'), (7, 407, '2026-03-23'), (8, 408, '2026-04-02'), (9, 409, '2026-04-10'), (10, 410, '2026-04-18');

        CREATE TABLE IF NOT EXISTS `tblhistorialmodificaciones` (
          `id_modificacion` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_cita` int(11) NOT NULL,
          `fecha_modificacion` date NOT NULL,
          `fecha_nueva` date NOT NULL,
          FOREIGN KEY (`id_cita`) REFERENCES `tblcita` (`id_cita`) ON DELETE CASCADE ON UPDATE CASCADE
        );

        INSERT OR IGNORE INTO `tblhistorialmodificaciones` (`id_modificacion`, `id_cita`, `fecha_modificacion`, `fecha_nueva`) VALUES
        (1, 202, '2026-03-08', '2026-03-10'),
        (2, 204, '2026-03-08', '2026-03-13'),
        (3, 210, '2026-03-10', '2026-03-15');

        CREATE TABLE IF NOT EXISTS `tblmetodopago` (
          `id_metodo` INTEGER PRIMARY KEY AUTOINCREMENT,
          `descripcion` varchar(50) NOT NULL UNIQUE
        );

        INSERT OR IGNORE INTO `tblmetodopago` (`id_metodo`, `descripcion`) VALUES
        (3, 'Efectivo'), (1, 'Tarjeta débito/crédito'), (2, 'Transferencia bancaria');

        CREATE TABLE IF NOT EXISTS `tblpago` (
          `id_pago` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_factura` int(11) NOT NULL,
          `id_metodo` int(11) NOT NULL,
          `pagado` tinyint(1) NOT NULL DEFAULT 0,
          `fecha_pago` date DEFAULT NULL,
          FOREIGN KEY (`id_factura`) REFERENCES `tblfactura` (`id_factura`) ON UPDATE CASCADE,
          FOREIGN KEY (`id_metodo`) REFERENCES `tblmetodopago` (`id_metodo`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_pago_factura` ON `tblpago` (`id_factura`);
        CREATE INDEX IF NOT EXISTS `idx_pago_pagado` ON `tblpago` (`pagado`);

        INSERT OR IGNORE INTO `tblpago` (`id_pago`, `id_factura`, `id_metodo`, `pagado`, `fecha_pago`) VALUES
        (501, 401, 1, 1, '2026-02-05'), (502, 402, 2, 0, NULL), (503, 403, 1, 0, NULL), (504, 404, 3, 1, '2026-03-10'), (505, 405, 1, 1, '2026-03-10'), (506, 406, 2, 0, NULL), (507, 407, 1, 0, NULL), (508, 408, 2, 1, '2026-04-04'), (509, 409, 3, 1, '2026-04-10'), (510, 410, 1, 0, NULL);

        CREATE TABLE IF NOT EXISTS `tblregistroclinico` (
          `id_registro` INTEGER PRIMARY KEY AUTOINCREMENT,
          `id_historial_clinico` int(11) NOT NULL,
          `id_odontologo` int(11) NOT NULL,
          `fecha` date NOT NULL,
          `notes` text DEFAULT NULL,
          FOREIGN KEY (`id_historial_clinico`) REFERENCES `tblhistorialclinico` (`id_historial_clinico`) ON DELETE CASCADE ON UPDATE CASCADE,
          FOREIGN KEY (`id_odontologo`) REFERENCES `tblusuario` (`id_usuario`) ON UPDATE CASCADE
        );

        CREATE INDEX IF NOT EXISTS `idx_rc_historial` ON `tblregistroclinico` (`id_historial_clinico`);

        INSERT OR IGNORE INTO `tblregistroclinico` (`id_registro`, `id_historial_clinico`, `id_odontologo`, `fecha`, `notes`) VALUES
        (1, 701, 3, '2026-02-05', 'Dolor leve al masticar'), (2, 702, 4, '2026-02-12', 'Inflamación encías'), (3, 703, 6, '2026-02-20', NULL), (4, 704, 4, '2026-03-03', 'Dolor intenso molar'), (5, 705, 3, '2026-03-10', 'Revisión general'), (6, 706, 4, '2026-03-18', 'Sangrado leve'), (7, 707, 5, '2026-03-23', 'Material a aceptar'), (8, 708, 3, '2026-04-02', 'Sin novedad'), (9, 709, 3, '2026-04-10', 'Infección controlada'), (10, 710, 4, '2026-04-18', 'Seguimiento tratamiento');
        """
        try:
            conn = sqlite3.connect(RUTA_BD)
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()
            print("🎉 ¡Éxito! Base de datos 'clinident.db' autoconstruida perfectamente con todas sus tablas y registros.")
        except Exception as e:
            print(f"❌ Error al intentar construir la base de datos interna: {e}")
    else:
        print(f"📁 Base de datos detectada con éxito en: {RUTA_BD} (No requiere recreación).")

# Ejecutamos la revisión y montaje de la BD antes de encender la aplicación
inicializar_base_de_datos()

# 2. CONFIGURACIÓN DE SEGURIDAD (CORS)
# Añadimos "null" para dar soporte completo a archivos locales abiertos con doble clic (file://)
CORS(app, supports_credentials=True, origins=["http://localhost", "http://127.0.0.1", "null"])

# 3. CONFIGURACIÓN DEL SISTEMA DE SESIONES
app.secret_key = 'clinident_secreto_ultra_seguro_123'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# 4. REGISTRAR LOS BLUEPRINTS
app.register_blueprint(login_blueprint, url_prefix='/login')
app.register_blueprint(recuperacion_blueprint, url_prefix='/login')
app.register_blueprint(registro_blueprint, url_prefix='/Registro')
app.register_blueprint(agenda_blueprint, url_prefix='/agenda_cliente')
app.register_blueprint(odontologo_blueprint, url_prefix='/odontologo')
app.register_blueprint(agenda_recepcion_blueprint, url_prefix='/agenda_recepcion')

@app.route('/', methods=['GET'])
def index():
    return {
        "status": "success",
        "message": "⚡ Servidor Clínico de Clinident corriendo perfectamente en Python ⚡"
    }


@app.route('/logout', methods=['POST'])
def logout():
    """ Destruye la sesión actual del usuario de forma segura """
    session.clear()  # Borra el id_usuario, nombre, etc. de la memoria
    return jsonify({"status": "success", "message": "Sesión eliminada con éxito"})


# --- MOTOR DE FRONTEND INTEGRADO CON PROTECCIÓN DE RUTAS (SOLO UNO) ---
@app.route('/web/<carpeta>/<archivo>', methods=['GET'])
def servir_frontend(carpeta, archivo):
    """
    Ruta dinámica para abrir la web. Incluye un sistema de protección
    para evitar accesos a páginas incorrectas según el estado de la sesión.
    """
    
    # 🚨 GUARDIA 1: Si ya inició sesión e intenta volver al Login, lo mandamos a la Agenda
    if carpeta == 'login' and archivo == 'login.html':
        if 'id_usuario' in session:
            print(f"🔄 Usuario con ID {session['id_usuario']} ya activo. Redirigiendo a la agenda.")
            return redirect('/web/agenda_cliente/index.html')

    # 🚨 GUARDIA 2: Si NO ha iniciado sesión e intenta meterse a la Agenda, lo mandamos al Login
    if carpeta == 'agenda_cliente' and archivo == 'index.html':
        if 'id_usuario' not in session:
            print("🚫 Intento de acceso no autorizado a la agenda. Redirigiendo al Login.")
            return redirect('/web/login/login.html')
        
    if carpeta == 'odontologo':
        if 'id_usuario' not in session:
            print("🚫 Acceso no autorizado al panel médico. Redirigiendo al Login.")
            return redirect('/web/login/login.html')
        if session.get('id_rol') != 2:
            print("🚫 Rol insuficiente para el panel médico.")
            return redirect('/web/login/login.html')

    # Si todo está en orden, sirve el archivo de forma normal
    carpeta_modulo = os.path.join(ruta_frontend, carpeta)
    return send_from_directory(carpeta_modulo, archivo)

    

# --- FUNCIÓN INTELIGENTE DE PORTABILIDAD ---
def encontrar_puerto_libre(puerto_inicial):
    """ Revisa si el puerto inicial está libre; si no, busca hacia arriba hasta hallar uno disponible. """
    puerto = puerto_inicial
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', puerto))
                return puerto  # El puerto está libre 🎉
            except socket.error:
                puerto += 1  # Puerto ocupado, probamos el siguiente

if __name__ == '__main__':
    if os.environ.get('FLASK_RUN_FROM_CLI') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        puerto_final = int(os.environ.get('CLINIDENT_PORT', 5000))
    else:
        puerto_final = encontrar_puerto_libre(5000)
        os.environ['CLINIDENT_PORT'] = str(puerto_final)

    print("\n" + "="*60)
    print(" 🚀 SERVIDOR CLÍNICO PYTHON (FLASK) PORTABLE EN MARCHA")
    print(f" 📌 Dirección local activa: http://127.0.0.1:{puerto_final}")
    print("="*60 + "\n")
    
    # CAMBIO AQUÍ: Cambiamos debug=True por debug=False para blindar el .exe
    app.run(debug=False, port=puerto_final)