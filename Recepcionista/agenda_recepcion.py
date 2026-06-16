import os
import sys
import sqlite3
from flask import Blueprint, request, jsonify, session
 
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
RUTA_BD = os.path.join(ruta_base, "clinident.db")
 
agenda_recepcion_blueprint = Blueprint('agenda_recepcion_blueprint', __name__)
 
 
def _migrar():
    conn = sqlite3.connect(RUTA_BD)
    try:
        conn.execute("ALTER TABLE tblcita ADD COLUMN tratamiento VARCHAR(100) DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    conn.execute("""
        UPDATE tblcita SET tratamiento = CASE
            WHEN id_sala = 4 THEN 'Cirugía Oral'
            WHEN id_sala = 5 THEN 'Limpieza Dental'
            WHEN id_sala = 3 THEN 'Ortodoncia'
            WHEN id_sala = 1 THEN 'Revisión General'
            ELSE 'Revisión General'
        END WHERE tratamiento IS NULL OR tratamiento = ''
    """)
    conn.commit()
    conn.close()
 
_migrar()
 
 
def _tiene_rol(id_usuario, *roles):
    """Devuelve True si el usuario tiene AL MENOS UNO de los roles indicados."""
    conn = sqlite3.connect(RUTA_BD)
    cur  = conn.cursor()
    placeholders = ",".join("?" * len(roles))
    cur.execute(f"""
        SELECT 1 FROM tblusuario_rol
        WHERE id_usuario = ? AND id_rol IN ({placeholders})
        UNION
        SELECT 1 FROM tblusuario
        WHERE id_usuario = ? AND id_rol IN ({placeholders})
        LIMIT 1
    """, [id_usuario, *roles, id_usuario, *roles])
    resultado = cur.fetchone() is not None
    conn.close()
    return resultado
 
 
def _roles_sesion():
    """Devuelve el set de roles del usuario en sesión."""
    return set(session.get('roles', [session.get('id_rol', 0)]))
 
 
def _es_admin_o_recepcion():
    roles = _roles_sesion()
    return bool(roles & {1, 3})   # 1=admin, 3=recepcionista
 
 
# 1. OBTENER PACIENTES
@agenda_recepcion_blueprint.route('/pacientes', methods=['GET'])
def obtener_pacientes():
    if not _es_admin_o_recepcion():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403
 
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    # Pacientes: quienes tengan rol 4 en cualquiera de las dos tablas
    cursor.execute("""
        SELECT DISTINCT u.id_usuario, u.nombre, u.apellido, u.correo
        FROM tblusuario u
        WHERE u.id_rol = 4
           OR EXISTS (
               SELECT 1 FROM tblusuario_rol ur
               WHERE ur.id_usuario = u.id_usuario AND ur.id_rol = 4
           )
        ORDER BY u.nombre ASC
    """)
    pacientes = [dict(row) for row in cursor.fetchall()]
    conexion.close()
    return jsonify({"status": "success", "data": pacientes})
 
 
# 2. AGENDAR CITA
@agenda_recepcion_blueprint.route('/agendar', methods=['POST'])
def agendar_cita_recepcionista():
    if not _es_admin_o_recepcion():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403
 
    data = request.get_json()
    id_usuario_existente = data.get('id_usuario_existente')
    nombre        = data.get('nombre',    '').strip()
    apellido      = data.get('apellido',  '').strip()
    telefono      = data.get('telefono',  '').strip()
    id_odontologo = data.get('id_odontologo')
    fecha         = data.get('fecha')
    hora          = data.get('hora')
    tratamiento   = data.get('tratamiento', '').strip() or None
 
    if not all([id_odontologo, fecha, hora]):
        return jsonify({"status": "error", "message": "Faltan campos obligatorios."}), 400
 
    # Validar que el odontólogo tenga rol 2 (o sea admin)
    if not _tiene_rol(id_odontologo, 1, 2):
        return jsonify({"status": "error",
                        "message": "El especialista seleccionado no tiene rol de Odontólogo."}), 400
 
    hora_inicio = f"{hora}:00"
    h, m = map(int, hora.split(':'))
    hora_fin = f"{str(h+1).zfill(2)}:{str(m).zfill(2)}:00"
 
    conexion = sqlite3.connect(RUTA_BD)
    cursor   = conexion.cursor()
 
    try:
        if not id_usuario_existente:
            if not nombre or not apellido:
                return jsonify({"status": "error",
                                "message": "Nombre y apellido son obligatorios."}), 400
 
            if telefono:
                cursor.execute("SELECT id_usuario FROM tblusuario WHERE telefono = ?", [telefono])
                if cursor.fetchone():
                    return jsonify({"status": "error",
                                    "message": "⚠️ Teléfono ya registrado. Busca al paciente en la lista."})
 
            correo_temp = f"{nombre.lower()}.{apellido.lower()}@clinident.temp"
            cursor.execute("""
                INSERT INTO tblusuario (nombre, apellido, correo, telefono, contrasena, id_rol, estado)
                VALUES (?, ?, ?, ?, '', 4, 'Activo')
            """, (nombre, apellido, correo_temp, telefono or None))
            id_paciente = cursor.lastrowid
 
            # Registrar también en tblusuario_rol
            cursor.execute("INSERT OR IGNORE INTO tblusuario_rol (id_usuario, id_rol) VALUES (?, 4)",
                           (id_paciente,))
        else:
            id_paciente = id_usuario_existente
 
        # Verificar conflicto de horario
        cursor.execute("""
            SELECT COUNT(*) FROM tblcita
            WHERE fecha = ? AND id_odontologo = ?
            AND ((hora_inicio <= ? AND hora_fin > ?)
              OR (hora_inicio <  ? AND hora_fin >= ?)
              OR (? <= hora_inicio AND ? > hora_inicio))
        """, [fecha, id_odontologo,
              hora_inicio, hora_inicio,
              hora_fin,    hora_fin,
              hora_inicio, hora_fin])
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error",
                            "message": "El especialista ya tiene una cita en ese horario."})
 
        cursor.execute("""
            INSERT INTO tblcita (fecha, hora_inicio, hora_fin, id_usuario, id_odontologo, id_sala, tratamiento)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (fecha, hora_inicio, hora_fin, id_paciente, id_odontologo, tratamiento))
        cursor.execute("INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 1)", (cursor.lastrowid,))
 
        conexion.commit()
        return jsonify({"status": "success", "message": "¡Cita registrada correctamente!"})
 
    except Exception as e:
        conexion.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conexion.close()