import sqlite3
from flask import Blueprint, jsonify, request, session
 
odontologo_blueprint = Blueprint('odontologo', __name__)
 
def get_db():
    from __main__ import RUTA_BD
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
 
 
# ── GUARDIA: odontólogos (rol 2) Y administradores (rol 1) ───────────────────
def verificar_odontologo():
    """Devuelve (id_usuario, None) si la sesión es válida, (None, respuesta_error) si no."""
    if 'id_usuario' not in session:
        return None, (jsonify({"status": "error", "message": "No autorizado"}), 401)
 
    # Leer roles desde sesión (lista) o fallback a id_rol legacy
    roles = set(session.get('roles', [session.get('id_rol', 0)]))
 
    if not roles & {1, 2}:   # rol 1=admin, rol 2=odontólogo
        return None, (jsonify({
            "status": "error",
            "message": "Tu sesión ha expirado o no tienes acceso. Por favor, inicia sesión de nuevo."
        }), 403)
 
    return session['id_usuario'], None
 
 
# ── MAPA DE ESTADOS VÁLIDOS QUE EL ODONTÓLOGO PUEDE ASIGNAR ───────────────────
# id_estado según tblestadocita: 1=programada, 2=cancelada, 3=reprogramada,
# 4=completada, 5=no_asistio
ESTADOS_PERMITIDOS = {
    "programada":  1,
    "completada":  4,
    "no_asistio":  5,
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 1. PERFIL DEL DOCTOR LOGUEADO
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
 
        return jsonify({"status": "success", "perfil": dict(row)})
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 2. CITAS DEL DÍA (o por fecha)
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/citas', methods=['GET'])
def citas_por_fecha():
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    fecha = request.args.get('fecha')
 
    conn = get_db()
    try:
        # ── NUEVO: se agregó LEFT JOIN hasta tbltratamiento/tblfactura para
        # poder calcular el campo `facturada` (1 si la cita ya tiene una
        # factura emitida, 0 si no). Esto es puramente informativo: NO
        # afecta ni reemplaza el estado clínico de la cita (`estado`), que
        # sigue siendo controlado únicamente por el odontólogo.
        sql = """
            SELECT c.id_cita,
                   c.fecha,
                   c.hora_inicio,
                   c.hora_fin,
                   u.nombre   || ' ' || u.apellido AS paciente,
                   s.nombre_sala,
                   COALESCE(e.nombre_estado, 'programada') AS estado,
                   a.motivo_cancelacion,
                   CASE WHEN f.id_factura IS NOT NULL THEN 1 ELSE 0 END AS facturada
            FROM   tblcita c
            JOIN   tblusuario  u ON u.id_usuario = c.id_usuario
            JOIN   tblsala     s ON s.id_sala    = c.id_sala
            LEFT JOIN tblagenda      a ON a.id_cita        = c.id_cita
            LEFT JOIN tblestadocita  e ON e.id_estado      = a.id_estado
            LEFT JOIN tbltratamiento t ON t.id_cita        = c.id_cita
            LEFT JOIN tblfactura     f ON f.id_tratamiento  = t.id_tratamiento
            WHERE  c.id_odontologo = ?
              AND  c.fecha = {}
            ORDER  BY c.hora_inicio
        """
        if fecha:
            rows = conn.execute(sql.format("?"), (id_usuario, fecha)).fetchall()
        else:
            rows = conn.execute(sql.format("DATE('now')"), (id_usuario,)).fetchall()
 
        return jsonify({
            "status": "success",
            "fecha":  fecha or "hoy",
            "total":  len(rows),
            "citas":  [dict(r) for r in rows]
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3. MARCAR CITA COMO COMPLETADA  (se mantiene por compatibilidad con el front
#    existente; internamente delega en la misma lógica de cambio de estado)
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/citas/<int:id_cita>/completar', methods=['PATCH'])
def completar_cita(id_cita):
    return _actualizar_estado_cita(id_cita, "completada")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 3-bis. CAMBIAR EL ESTADO DE UNA CITA (completada / no_asistio / programada)
#    Body JSON esperado: { "estado": "completada" | "no_asistio" | "programada" }
#    Permite revertir un estado anterior (p. ej. de "no_asistio" volver a
#    "programada" si el odontólogo se equivocó al marcarla).
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/citas/<int:id_cita>/estado', methods=['PATCH'])
def cambiar_estado_cita(id_cita):
    body = request.get_json(silent=True) or {}
    estado = (body.get('estado') or '').strip().lower()
 
    if estado not in ESTADOS_PERMITIDOS:
        return jsonify({
            "status": "error",
            "message": f"Estado '{estado}' no es válido. Usa: {', '.join(ESTADOS_PERMITIDOS.keys())}"
        }), 400
 
    return _actualizar_estado_cita(id_cita, estado)
 
 
def _actualizar_estado_cita(id_cita, estado):
    """Lógica compartida: valida pertenencia de la cita al odontólogo logueado
    y actualiza (o inserta) su registro en tblagenda con el id_estado correspondiente."""
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    id_estado = ESTADOS_PERMITIDOS[estado]
 
    conn = get_db()
    try:
        cita = conn.execute("""
            SELECT id_cita FROM tblcita
            WHERE id_cita = ? AND id_odontologo = ?
        """, (id_cita, id_usuario)).fetchone()
 
        if not cita:
            return jsonify({
                "status": "error",
                "message": "Cita no encontrada o no pertenece a este odontólogo"
            }), 404
 
        en_agenda = conn.execute(
            "SELECT id_estado FROM tblagenda WHERE id_cita = ?", (id_cita,)
        ).fetchone()
 
        if en_agenda:
            conn.execute("UPDATE tblagenda SET id_estado = ? WHERE id_cita = ?", (id_estado, id_cita))
        else:
            conn.execute("INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, ?)", (id_cita, id_estado))
 
        conn.commit()
 
        mensajes = {
            "completada": f"Cita {id_cita} marcada como completada",
            "no_asistio": f"Cita {id_cita} marcada como 'no asistió'",
            "programada": f"Cita {id_cita} reactivada como programada",
        }
 
        return jsonify({
            "status": "success",
            "estado": estado,
            "message": mensajes.get(estado, f"Cita {id_cita} actualizada a '{estado}'")
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 4. TODAS LAS CITAS (con filtro opcional de estado)
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/todas_citas', methods=['GET'])
def todas_las_citas():
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    estado = request.args.get('estado', '').strip().lower()
 
    conn = get_db()
    try:
        # ── NUEVO: mismo agregado de `facturada` que en citas_por_fecha().
        sql = """
            SELECT c.id_cita,
                   c.fecha,
                   c.hora_inicio,
                   c.hora_fin,
                   u.nombre || ' ' || u.apellido AS paciente,
                   s.nombre_sala,
                   COALESCE(e.nombre_estado, 'programada') AS estado,
                   a.motivo_cancelacion,
                   CASE WHEN f.id_factura IS NOT NULL THEN 1 ELSE 0 END AS facturada
            FROM   tblcita c
            JOIN   tblusuario       u ON u.id_usuario       = c.id_usuario
            JOIN   tblsala          s ON s.id_sala          = c.id_sala
            LEFT JOIN tblagenda      a ON a.id_cita         = c.id_cita
            LEFT JOIN tblestadocita  e ON e.id_estado       = a.id_estado
            LEFT JOIN tbltratamiento t ON t.id_cita         = c.id_cita
            LEFT JOIN tblfactura     f ON f.id_tratamiento   = t.id_tratamiento
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
            "total":  len(rows),
            "citas":  [dict(r) for r in rows]
        })
    finally:
        conn.close()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 5. HISTORIAL CLÍNICO DE UN PACIENTE
# ─────────────────────────────────────────────────────────────────────────────
@odontologo_blueprint.route('/historial/<int:id_paciente>', methods=['GET'])
def historial_paciente(id_paciente):
    id_usuario, err = verificar_odontologo()
    if err:
        return err
 
    conn = get_db()
    try:
        paciente = conn.execute("""
            SELECT id_usuario, nombre, apellido, correo, telefono
            FROM   tblusuario
            WHERE  id_usuario = ?
              AND (id_rol = 4 OR EXISTS (
                  SELECT 1 FROM tblusuario_rol ur
                  WHERE ur.id_usuario = tblusuario.id_usuario AND ur.id_rol = 4
              ))
        """, (id_paciente,)).fetchone()
 
        if not paciente:
            return jsonify({"status": "error", "message": "Paciente no encontrado"}), 404
 
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
            "status":          "success",
            "paciente":        dict(paciente),
            "total_registros": len(registros),
            "historial":       [dict(r) for r in registros]
        })
    finally:
        conn.close()