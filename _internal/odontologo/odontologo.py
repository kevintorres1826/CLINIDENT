import sqlite3
from flask import Blueprint, jsonify, request, session
 
odontologo_blueprint = Blueprint('odontologo', __name__)
 
# ── Ruta a la BD (se inyecta desde main.py al importar) ──────────────────────
def get_db():
    from __main__ import RUTA_BD
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row          # Acceso por nombre de columna
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
 
 
# ── GUARDIA: sólo odontólogos activos pueden usar estas rutas ─────────────────
def verificar_odontologo():
    """Devuelve (id_usuario, None) si la sesión es válida, (None, respuesta_error) si no."""
    if 'id_usuario' not in session:
        return None, (jsonify({"status": "error", "message": "No autorizado"}), 401)
    if session.get('id_rol') != 2:          # rol 2 = odontologo
        return None, (jsonify({"status": "error", "message": "Acceso restringido a odontólogos"}), 403)
    return session['id_usuario'], None
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 1. PERFIL DEL DOCTOR LOGUEADO
#    GET /odontologo/perfil
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/perfil', methods=['GET'])
def perfil():
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido, u.correo, u.telefono,
                   r.rol, u.estado
            FROM   tblusuario u
            JOIN   tblrol r ON r.id_rol = u.id_rol
            WHERE  u.id_usuario = ?
        """, (id_usuario,)).fetchone()
 
        if not row:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
 
        return jsonify({
            "status": "success",
            "perfil": dict(row)
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2. CITAS DEL DÍA (o por fecha)
#    GET /odontologo/citas?fecha=YYYY-MM-DD
#    Si no se pasa ?fecha se usa la fecha actual del servidor.
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/citas', methods=['GET'])
def citas_por_fecha():
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    fecha = request.args.get('fecha')       # Ej: ?fecha=2026-06-05
 
    conn = get_db()
    try:
        # Si no viene fecha usamos DATE('now') de SQLite
        if fecha:
            rows = conn.execute("""
                SELECT c.id_cita,
                       c.fecha,
                       c.hora_inicio,
                       c.hora_fin,
                       u.nombre   || ' ' || u.apellido AS paciente,
                       s.nombre_sala,
                       e.nombre_estado AS estado
                FROM   tblcita c
                JOIN   tblusuario  u ON u.id_usuario = c.id_usuario
                JOIN   tblsala     s ON s.id_sala    = c.id_sala
                LEFT JOIN tblagenda   a ON a.id_cita   = c.id_cita
                LEFT JOIN tblestadocita e ON e.id_estado = a.id_estado
                WHERE  c.id_odontologo = ?
                  AND  c.fecha = ?
                ORDER  BY c.hora_inicio
            """, (id_usuario, fecha)).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.id_cita,
                       c.fecha,
                       c.hora_inicio,
                       c.hora_fin,
                       u.nombre   || ' ' || u.apellido AS paciente,
                       s.nombre_sala,
                       e.nombre_estado AS estado
                FROM   tblcita c
                JOIN   tblusuario  u ON u.id_usuario = c.id_usuario
                JOIN   tblsala     s ON s.id_sala    = c.id_sala
                LEFT JOIN tblagenda   a ON a.id_cita   = c.id_cita
                LEFT JOIN tblestadocita e ON e.id_estado = a.id_estado
                WHERE  c.id_odontologo = ?
                  AND  c.fecha = DATE('now')
                ORDER  BY c.hora_inicio
            """, (id_usuario,)).fetchall()
 
        return jsonify({
            "status": "success",
            "fecha": fecha or "hoy",
            "total": len(rows),
            "citas": [dict(r) for r in rows]
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3. MARCAR CITA COMO COMPLETADA (atendida)
#    PATCH /odontologo/citas/<id_cita>/completar
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/citas/<int:id_cita>/completar', methods=['PATCH'])
def completar_cita(id_cita):
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    conn = get_db()
    try:
        # Verificar que la cita pertenece a este odontólogo
        cita = conn.execute("""
            SELECT id_cita FROM tblcita
            WHERE id_cita = ? AND id_odontologo = ?
        """, (id_cita, id_usuario)).fetchone()
 
        if not cita:
            return jsonify({
                "status": "error",
                "message": "Cita no encontrada o no pertenece a este odontólogo"
            }), 404
 
        # Verificar que la cita existe en tblagenda
        en_agenda = conn.execute(
            "SELECT id_estado FROM tblagenda WHERE id_cita = ?", (id_cita,)
        ).fetchone()
 
        if en_agenda:
            # Ya existe: actualizamos el estado a 4 (completada)
            conn.execute("""
                UPDATE tblagenda SET id_estado = 4 WHERE id_cita = ?
            """, (id_cita,))
        else:
            # No existe en agenda: la insertamos como completada
            conn.execute("""
                INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 4)
            """, (id_cita,))
 
        conn.commit()
        return jsonify({
            "status": "success",
            "message": f"Cita {id_cita} marcada como completada"
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 4. TODAS LAS CITAS (sin filtro de fecha, con filtro opcional de estado)
#    GET /odontologo/todas_citas
#    GET /odontologo/todas_citas?estado=completada
#    GET /odontologo/todas_citas?estado=programada
#    GET /odontologo/todas_citas?estado=cancelada
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/todas_citas', methods=['GET'])
def todas_las_citas():
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    estado = request.args.get('estado', '').strip().lower()  # Ej: ?estado=completada
 
    conn = get_db()
    try:
        sql = """
            SELECT c.id_cita,
                   c.fecha,
                   c.hora_inicio,
                   c.hora_fin,
                   u.nombre || ' ' || u.apellido AS paciente,
                   s.nombre_sala,
                   COALESCE(e.nombre_estado, 'programada') AS estado
            FROM   tblcita c
            JOIN   tblusuario     u ON u.id_usuario = c.id_usuario
            JOIN   tblsala        s ON s.id_sala    = c.id_sala
            LEFT JOIN tblagenda   a ON a.id_cita    = c.id_cita
            LEFT JOIN tblestadocita e ON e.id_estado = a.id_estado
            WHERE  c.id_odontologo = ?
        """
        params = [id_usuario]
 
        if estado:
            sql += " AND LOWER(COALESCE(e.nombre_estado, 'programada')) = ?"
            params.append(estado)
 
        sql += " ORDER BY c.fecha DESC, c.hora_inicio ASC"
 
        rows = conn.execute(sql, params).fetchall()
 
        return jsonify({
            "status": "success",
            "filtro": estado or "todas",
            "total": len(rows),
            "citas": [dict(r) for r in rows]
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 5. HISTORIAL CLÍNICO DE UN PACIENTE
#    GET /odontologo/historial/<id_paciente>
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/historial/<int:id_paciente>', methods=['GET'])
def historial_paciente(id_paciente):
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    conn = get_db()
    try:
        # Datos básicos del paciente
        paciente = conn.execute("""
            SELECT id_usuario, nombre, apellido, correo, telefono
            FROM   tblusuario
            WHERE  id_usuario = ? AND id_rol = 4
        """, (id_paciente,)).fetchone()
 
        if not paciente:
            return jsonify({"status": "error", "message": "Paciente no encontrado"}), 404
 
        # Historial clínico completo
        registros = conn.execute("""
            SELECT hc.id_historial_clinico,
                   hc.fecha,
                   hc.observaciones,
                   tt.nombre          AS tipo_tratamiento,
                   t.diagnostico,
                   t.valor,
                   c.fecha            AS fecha_cita,
                   c.hora_inicio,
                   c.hora_fin,
                   s.nombre_sala,
                   e.nombre_estado    AS estado_cita
            FROM   tblhistorialclinico hc
            JOIN   tbltratamiento      t  ON t.id_tratamiento = hc.id_tratamiento
            JOIN   tbltipotratamiento  tt ON tt.id_tipo        = t.id_tipo
            JOIN   tblcita             c  ON c.id_cita         = hc.id_cita
            JOIN   tblsala             s  ON s.id_sala         = c.id_sala
            LEFT JOIN tblagenda        a  ON a.id_cita         = c.id_cita
            LEFT JOIN tblestadocita    e  ON e.id_estado       = a.id_estado
            WHERE  t.id_usuario = ?
            ORDER  BY hc.fecha DESC
        """, (id_paciente,)).fetchall()
 
        return jsonify({
            "status": "success",
            "paciente": dict(paciente),
            "total_registros": len(registros),
            "historial": [dict(r) for r in registros]
        })
    finally:
        conn.close()
 