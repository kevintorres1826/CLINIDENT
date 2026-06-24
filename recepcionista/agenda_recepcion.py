import os
import sys
import sqlite3
from datetime import datetime, timedelta
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


# ── DURACIONES POR TRATAMIENTO (minutos) ─────────────────────────────────────
DURACIONES = {
    "ortodoncia":      60,
    "endodoncia":      90,
    "blanqueamiento":  90,
    "cirugía oral":   120,
    "revisión general": 30,
    "limpieza dental":  45,
}

HORARIOS_MAESTROS = [
    "08:00 AM", "08:45 AM", "09:30 AM", "10:15 AM", "11:00 AM", "11:45 AM",
    "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM"
]


def _minutos_tratamiento(nombre):
    return DURACIONES.get(nombre.lower().strip(), 45)


def _roles_sesion():
    return set(session.get('roles', [session.get('id_rol', 0)]))


def _es_admin_o_recepcion():
    return bool(_roles_sesion() & {1, 3})


def _tiene_rol(id_usuario, *roles):
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


# ── LÓGICA DE ESPECIALISTAS (duplicada de agenda_cliente) ────────────────────

def _odontologos_disponibles():
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT u.id_usuario, u.nombre, u.apellido
        FROM tblusuario u
        WHERE u.estado = 'Activo'
          AND (
              u.id_rol = 2
              OR EXISTS (
                  SELECT 1 FROM tblusuario_rol ur
                  WHERE ur.id_usuario = u.id_usuario AND ur.id_rol = 2
              )
          )
        ORDER BY u.nombre ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"id": r["id_usuario"], "nombre": f"Dr. {r['nombre']} {r['apellido']}"} for r in rows]


def _odontologos_por_tratamiento(nombre_tratamiento):
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("SELECT id_tipo FROM tbltipotratamiento WHERE LOWER(nombre) = LOWER(?)",
                [nombre_tratamiento])
    fila = cur.fetchone()
    if not fila:
        conn.close()
        return _odontologos_disponibles()

    id_tipo = fila["id_tipo"]
    cur.execute("""
        SELECT DISTINCT u.id_usuario, u.nombre, u.apellido
        FROM tblusuario u
        INNER JOIN tblodontologo_servicio os ON u.id_usuario = os.id_odontologo
        WHERE os.id_tipo = ? AND u.estado = 'Activo'
        ORDER BY u.nombre ASC
    """, [id_tipo])
    rows = cur.fetchall()
    conn.close()
    resultado = [{"id": r["id_usuario"], "nombre": f"Dr. {r['nombre']} {r['apellido']}"} for r in rows]
    return resultado if resultado else _odontologos_disponibles()


def _sala_de_doctor(id_doctor):
    conn = sqlite3.connect(RUTA_BD)
    cur  = conn.cursor()
    cur.execute("SELECT id_sala FROM tblodontologo_sala WHERE id_odontologo = ?", [id_doctor])
    fila = cur.fetchone()
    conn.close()
    return fila[0] if fila else None


def _elegir_doctor(candidatos, fecha, hora_inicio, hora_fin, excluir_id_cita=None):
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    libres = []

    for doc in candidatos:
        id_doc  = doc["id"]
        id_sala = _sala_de_doctor(id_doc)
        if id_sala is None:
            continue

        sql = """
            SELECT COUNT(*) FROM tblcita c
            LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
            WHERE c.fecha = ?
              AND (a.id_estado IS NULL OR a.id_estado != 2)
              AND c.id_odontologo = ?
              AND c.hora_inicio < ?
              AND c.hora_fin    > ?
        """
        params = [fecha, id_doc, hora_fin, hora_inicio]
        if excluir_id_cita:
            sql += " AND c.id_cita != ?"
            params.append(excluir_id_cita)

        cur.execute(sql, params)
        if cur.fetchone()[0] > 0:
            continue

        cur.execute("""
            SELECT COUNT(*) FROM tblcita c
            LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
            WHERE c.fecha = ? AND c.id_odontologo = ?
              AND (a.id_estado IS NULL OR a.id_estado != 2)
        """, [fecha, id_doc])
        carga = cur.fetchone()[0]
        libres.append((carga, doc["nombre"], id_doc, id_sala))

    conn.close()
    if not libres:
        return None
    libres.sort(key=lambda x: (x[0], x[1]))
    mejor = libres[0]
    return {"id_odontologo": mejor[2], "id_sala": mejor[3]}


def _nombre_doctor(id_odontologo):
    conn = sqlite3.connect(RUTA_BD)
    cur  = conn.cursor()
    cur.execute("SELECT nombre, apellido FROM tblusuario WHERE id_usuario = ?", [id_odontologo])
    row = cur.fetchone()
    conn.close()
    return f"Dr. {row[0]} {row[1]}" if row else "Especialista"


# ── HORAS OCUPADAS (para el grid visual del recepcionista) ───────────────────

def _horas_ocupadas(fecha, nombre_tratamiento, id_paciente=None, excluir_id_cita=None):
    candidatos     = _odontologos_por_tratamiento(nombre_tratamiento)
    ids_candidatos = [c["id"] for c in candidatos]
    if not ids_candidatos:
        return []

    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()

    # Citas de los candidatos ese día
    placeholders = ",".join("?" * len(ids_candidatos))
    sql_doc = f"""
        SELECT c.hora_inicio, c.hora_fin, c.id_odontologo FROM tblcita c
        LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
        WHERE c.fecha = ?
          AND (a.id_estado IS NULL OR a.id_estado != 2)
          AND c.id_odontologo IN ({placeholders})
    """
    params_doc = [fecha] + ids_candidatos
    if excluir_id_cita:
        sql_doc += " AND c.id_cita != ?"
        params_doc.append(excluir_id_cita)
    cur.execute(sql_doc, params_doc)
    citas_doctores = cur.fetchall()

    # Citas del paciente ese día (para bloquear solapamientos)
    citas_paciente = []
    if id_paciente:
        sql_pac = """
            SELECT c.hora_inicio, c.hora_fin FROM tblcita c
            LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
            WHERE c.fecha = ? AND c.id_usuario = ?
              AND (a.id_estado IS NULL OR a.id_estado != 2)
        """
        params_pac = [fecha, id_paciente]
        if excluir_id_cita:
            sql_pac += " AND c.id_cita != ?"
            params_pac.append(excluir_id_cita)
        cur.execute(sql_pac, params_pac)
        citas_paciente = cur.fetchall()

    conn.close()

    minutos  = _minutos_tratamiento(nombre_tratamiento)
    ocupadas = []

    for hora_str in HORARIOS_MAESTROS:
        slot_dt   = datetime.strptime(hora_str, "%I:%M %p")
        slot_fin  = slot_dt + timedelta(minutes=minutos)

        # Bloquear si el paciente ya tiene algo que solape
        paciente_ocupado = any(
            datetime.strptime(r["hora_inicio"], "%H:%M:%S") < slot_fin and
            datetime.strptime(r["hora_fin"],    "%H:%M:%S") > slot_dt
            for r in citas_paciente
        )
        if paciente_ocupado:
            ocupadas.append(hora_str)
            continue

        # Bloquear si TODOS los candidatos están ocupados en ese slot
        ocupados_slot = {
            r["id_odontologo"] for r in citas_doctores
            if datetime.strptime(r["hora_inicio"], "%H:%M:%S") < slot_fin and
               datetime.strptime(r["hora_fin"],    "%H:%M:%S") > slot_dt
        }
        if len(ocupados_slot) >= len(ids_candidatos):
            ocupadas.append(hora_str)

    return ocupadas


# =========================================================================
# ─── RUTAS
# =========================================================================

@agenda_recepcion_blueprint.route('/pacientes', methods=['GET'])
def obtener_pacientes():
    if not _es_admin_o_recepcion():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT u.id_usuario, u.nombre, u.apellido, u.correo, u.telefono
        FROM tblusuario u
        WHERE u.id_rol = 4
           OR EXISTS (
               SELECT 1 FROM tblusuario_rol ur
               WHERE ur.id_usuario = u.id_usuario AND ur.id_rol = 4
           )
        ORDER BY u.nombre ASC
    """)
    pacientes = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"status": "success", "data": pacientes})


@agenda_recepcion_blueprint.route('/odontologos_por_tratamiento', methods=['GET'])
def odontologos_por_tratamiento():
    if not _es_admin_o_recepcion():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403
    tratamiento = request.args.get('tratamiento', '').strip()
    if not tratamiento:
        return jsonify({"status": "error", "message": "Parámetro requerido."})
    return jsonify({"status": "success", "data": _odontologos_por_tratamiento(tratamiento)})


@agenda_recepcion_blueprint.route('/horas_ocupadas', methods=['GET'])
def horas_ocupadas():
    if not _es_admin_o_recepcion():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403
    fecha       = request.args.get('fecha', '')
    tratamiento = request.args.get('tratamiento', '')
    id_paciente = request.args.get('id_paciente', None)
    if id_paciente:
        try: id_paciente = int(id_paciente)
        except: id_paciente = None
    if not fecha or not tratamiento:
        return jsonify({"status": "success", "data": []})
    ocupadas = _horas_ocupadas(fecha, tratamiento, id_paciente=id_paciente)
    return jsonify({"status": "success", "data": ocupadas})


@agenda_recepcion_blueprint.route('/agendar', methods=['POST'])
def agendar_cita_recepcionista():
    if not _es_admin_o_recepcion():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    data = request.get_json()
    id_usuario_existente = data.get('id_usuario_existente')
    nombre      = data.get('nombre',    '').strip()
    apellido    = data.get('apellido',  '').strip()
    telefono    = data.get('telefono',  '').strip()
    fecha       = data.get('fecha',     '')
    hora_raw    = data.get('hora',      '')        # "08:00 AM"
    tratamiento = data.get('tratamiento', '').strip()

    if not all([fecha, hora_raw, tratamiento]):
        return jsonify({"status": "error", "message": "Faltan campos obligatorios."}), 400

    # Calcular hora_inicio y hora_fin con duración real
    hora_obj    = datetime.strptime(hora_raw, "%I:%M %p")
    hora_inicio = hora_obj.strftime("%H:%M:%S")
    hora_fin    = (hora_obj + timedelta(minutes=_minutos_tratamiento(tratamiento))).strftime("%H:%M:%S")

    conn   = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()

    try:
        # ── Resolver paciente ─────────────────────────────────────────────
        if not id_usuario_existente:
            if not nombre or not apellido:
                return jsonify({"status": "error",
                                "message": "Nombre y apellido son obligatorios."}), 400

            # Intentar unión por teléfono si ya existe una cuenta
            id_paciente = None
            if telefono:
                cursor.execute("SELECT id_usuario FROM tblusuario WHERE telefono = ?", [telefono])
                fila = cursor.fetchone()
                if fila:
                    id_paciente = fila[0]

            if not id_paciente:
                correo_temp = f"{nombre.lower()}.{apellido.lower()}@clinident.temp"
                cursor.execute("""
                    INSERT INTO tblusuario
                        (nombre, apellido, correo, telefono, contrasena, id_rol, estado)
                    VALUES (?, ?, ?, ?, '', 4, 'Activo')
                """, (nombre, apellido, correo_temp, telefono or None))
                id_paciente = cursor.lastrowid
                cursor.execute(
                    "INSERT OR IGNORE INTO tblusuario_rol (id_usuario, id_rol) VALUES (?, 4)",
                    (id_paciente,)
                )
        else:
            id_paciente = int(id_usuario_existente)

        # ── Validar solapamiento del paciente ─────────────────────────────
        cursor.execute("""
            SELECT COUNT(*) FROM tblcita c
            LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
            WHERE c.fecha      = ?
              AND c.id_usuario = ?
              AND (a.id_estado IS NULL OR a.id_estado != 2)
              AND c.hora_inicio < ?
              AND c.hora_fin    > ?
        """, [fecha, id_paciente, hora_fin, hora_inicio])
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error",
                            "message": "El paciente ya tiene una cita en ese horario."})

        # ── Elegir doctor disponible ──────────────────────────────────────
        candidatos = _odontologos_por_tratamiento(tratamiento)
        if not candidatos:
            return jsonify({"status": "error",
                            "message": "No hay especialistas para este tratamiento."})

        asignacion = _elegir_doctor(candidatos, fecha, hora_inicio, hora_fin)
        if asignacion is None:
            return jsonify({"status": "error",
                            "message": "Todos los especialistas están ocupados en ese horario."})

        id_odontologo = asignacion["id_odontologo"]
        id_sala       = asignacion["id_sala"]

        # ── Insertar cita ─────────────────────────────────────────────────
        cursor.execute("""
            INSERT INTO tblcita
                (fecha, hora_inicio, hora_fin, id_usuario, id_odontologo, id_sala, tratamiento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fecha, hora_inicio, hora_fin, id_paciente, id_odontologo, id_sala, tratamiento))
        cursor.execute(
            "INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 1)", (cursor.lastrowid,)
        )

        conn.commit()
        return jsonify({
            "status":          "success",
            "message":         f"¡Cita registrada! Asignado: {_nombre_doctor(id_odontologo)}",
            "doctor_asignado": _nombre_doctor(id_odontologo)
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()