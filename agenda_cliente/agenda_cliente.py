import os
import sys
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session

print("=== VERSION NUEVA agenda_cliente.py ===")
print("=== AGENDA CLIENTE CARGADO ===")

if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_BD = os.path.join(ruta_base, "clinident.db")

agenda_blueprint = Blueprint('agenda_blueprint', __name__)


def _migrar():
    conn = sqlite3.connect(RUTA_BD)

    # ── Migración 1: columna 'tratamiento' en tblcita ──────────────────────
    try:
        conn.execute("ALTER TABLE tblcita ADD COLUMN tratamiento VARCHAR(100) DEFAULT NULL")
        conn.commit()
        print("✅ Migración: columna 'tratamiento' agregada a tblcita")
    except Exception:
        pass

    conn.execute("""
        UPDATE tblcita SET tratamiento = CASE
            WHEN id_sala = 4 THEN 'Cirugía oral'
            WHEN id_sala = 5 THEN 'Limpieza dental'
            WHEN id_sala = 3 THEN 'Ortodoncia'
            WHEN id_sala = 1 THEN 'Revisión general'
            ELSE 'Revisión general'
        END
        WHERE tratamiento IS NULL OR tratamiento = ''
    """)
    conn.commit()

    # ── Migración 2: columna 'motivo_cancelacion' en tblagenda ─────────────
    try:
        conn.execute("ALTER TABLE tblagenda ADD COLUMN motivo_cancelacion TEXT DEFAULT NULL")
        conn.commit()
        print("✅ Migración: columna 'motivo_cancelacion' agregada a tblagenda")
    except Exception:
        pass

    conn.close()


_migrar()


def obtener_odontologos_disponibles():
    """
    Devuelve todos los odontólogos activos (rol 2).
    Se usa como fallback cuando no hay especialistas para un tratamiento.
    """
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("""
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
    odontologos = cursor.fetchall()
    conexion.close()
    return [{"id": o['id_usuario'], "nombre": f"Dr. {o['nombre']} {o['apellido']}"} for o in odontologos]


def obtener_odontologos_por_tratamiento(nombre_tratamiento, excluir_id=None):
    """
    Devuelve los odontólogos activos que tienen asignado el tratamiento indicado
    en tblodontologo_servicio. Si no hay ninguno, hace fallback a todos los odontólogos.
    """
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    # Buscar id_tipo por nombre (case-insensitive)
    cursor.execute("""
        SELECT id_tipo FROM tbltipotratamiento
        WHERE LOWER(nombre) = LOWER(?)
    """, [nombre_tratamiento])
    fila = cursor.fetchone()

    if not fila:
        conexion.close()
        todos = obtener_odontologos_disponibles()
        if excluir_id:
            todos = [o for o in todos if o['id'] != excluir_id]
        return todos

    id_tipo = fila['id_tipo']

    cursor.execute("""
        SELECT DISTINCT u.id_usuario, u.nombre, u.apellido
        FROM tblusuario u
        INNER JOIN tblodontologo_servicio os ON u.id_usuario = os.id_odontologo
        WHERE os.id_tipo = ?
          AND u.estado = 'Activo'
        ORDER BY u.nombre ASC
    """, [id_tipo])

    especialistas = cursor.fetchall()
    conexion.close()

    resultado = [
        {"id": e['id_usuario'], "nombre": f"Dr. {e['nombre']} {e['apellido']}"}
        for e in especialistas
        if (excluir_id is None or e['id_usuario'] != excluir_id)
    ]

    # Fallback: si no hay especialistas asignados para ese tratamiento
    if not resultado:
        todos = obtener_odontologos_disponibles()
        if excluir_id:
            todos = [o for o in todos if o['id'] != excluir_id]
        return todos

    return resultado


def obtener_sala_de_doctor(id_doctor):
    """
    Devuelve el id_sala (consultorio propio) de un odontólogo específico.
    Cada odontólogo tiene su propio consultorio (relación 1 a 1 en
    tblodontologo_sala), así que dos doctores nunca compiten por la
    misma sala física. Si no tiene sala asignada (caso raro, odontólogo
    recién creado antes de que corra la migración), devuelve None.
    """
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id_sala FROM tblodontologo_sala WHERE id_odontologo = ?",
        [id_doctor]
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila[0] if fila else None


def elegir_doctor_disponible(candidatos, fecha, hora_inicio, hora_fin, excluir_id_cita=None):
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    libres_con_carga = []

    for doc in candidatos:
        id_doc = doc['id']
        id_sala_doc = obtener_sala_de_doctor(id_doc)

        if id_sala_doc is None:
            continue

        check_sql = """
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
            check_sql += " AND c.id_cita != ?"
            params.append(excluir_id_cita)

        cursor.execute(check_sql, params)
        ocupado = cursor.fetchone()[0] > 0

        if not ocupado:
            cursor.execute("""
                SELECT COUNT(*) FROM tblcita c
                LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                WHERE c.fecha = ? AND c.id_odontologo = ?
                  AND (a.id_estado IS NULL OR a.id_estado != 2)
            """, [fecha, id_doc])
            carga = cursor.fetchone()[0]
            libres_con_carga.append((carga, doc['nombre'], id_doc, id_sala_doc))

    conexion.close()

    if not libres_con_carga:
        return None

    libres_con_carga.sort(key=lambda x: (x[0], x[1]))
    mejor = libres_con_carga[0]
    return {"id_odontologo": mejor[2], "id_sala": mejor[3]}


def obtener_sala_segun_tratamiento(tratamiento_name):
    """
    LEGACY: ya no se usa para asignar la sala de una cita nueva (eso ahora
    depende del consultorio propio del doctor elegido, ver
    obtener_sala_de_doctor / elegir_doctor_disponible). Se conserva por si
    algún código viejo todavía la referencia.
    """
    nombre = tratamiento_name.lower().strip()
    if nombre == "cirugía oral":    return 4
    if nombre == "limpieza dental": return 5
    if nombre == "ortodoncia":      return 3
    return 2


def obtener_nombre_doctor_js(id_odontologo):
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, apellido FROM tblusuario WHERE id_usuario = ?", [id_odontologo])
    doc = cursor.fetchone()
    conexion.close()
    return f"Dr. {doc[0]} {doc[1]}" if doc else "Especialista"


def icono_para_tratamiento(nombre):
    iconos = {
        "Cirugía oral":     "🔬",
        "Cirugía Oral":     "🔬",
        "Limpieza dental":  "🦷",
        "Limpieza Dental":  "🦷",
        "Ortodoncia":       "😁",
        "Endodoncia":       "💉",
        "Revisión general": "🩺",
        "Revisión General": "🩺",
        "Blanqueamiento":   "✨",
    }
    return iconos.get(nombre, "🦷")


# =========================================================================
# ─── ACCIONES GET
# =========================================================================

@agenda_blueprint.route('/agenda_cliente', methods=['GET'])
def acciones_get():
    id_usuario_sesion     = session.get('id_usuario', 3)
    nombre_usuario_sesion = session.get('nombre_usuario', session.get('nombre', 'Paciente'))
    action                = request.args.get('action', '')

    # ── Sesión del usuario ────────────────────────────────────────────────
    if action == 'get_sesion_usuario':
        roles = session.get('roles', None)
        if not roles:
            id_rol_legacy = session.get('id_rol')
            roles = [id_rol_legacy] if id_rol_legacy else []

        return jsonify({
            "status": "success",
            "id":     id_usuario_sesion,
            "nombre": nombre_usuario_sesion,
            "id_rol": session.get('id_rol'),
            "roles":  roles
        })

    # ── Odontólogos filtrados por tratamiento (ASIGNACIÓN AUTOMÁTICA) ─────
    elif action == 'get_odontologos_por_tratamiento':
        nombre_tratamiento = request.args.get('tratamiento', '').strip()
        if not nombre_tratamiento:
            return jsonify({"status": "error", "message": "Parámetro 'tratamiento' requerido."})

        especialistas = obtener_odontologos_por_tratamiento(
            nombre_tratamiento,
            excluir_id=id_usuario_sesion
        )
        return jsonify({"status": "success", "data": especialistas})

    # ── Todos los odontólogos (fallback / uso interno) ────────────────────
    elif action == 'get_odontologos':
        todos = [
            o for o in obtener_odontologos_disponibles()
            if o['id'] != id_usuario_sesion
        ]
        return jsonify({"status": "success", "data": todos})

    # ── Precios de tratamientos ───────────────────────────────────────────
    elif action == 'get_tratamientos':
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT nombre, COALESCE(precio_base, 0) AS precio_base
                FROM tbltipotratamiento
            """)
            precios = {fila['nombre']: fila['precio_base'] for fila in cursor.fetchall()}
            return jsonify({"status": "success", "data": precios})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion: conexion.close()

    # ── Horas ocupadas para fecha + tratamiento (TODOS los candidatos) ────
    elif action == 'get_citas_ocupadas':
        fecha       = request.args.get('fecha', '')
        tratamiento = request.args.get('tratamiento', '')
        edit_id     = request.args.get('edit_id', '')

        if not fecha or not tratamiento:
            return jsonify({"status": "success", "data": []})

        conexion = None
        try:
            candidatos = obtener_odontologos_por_tratamiento(tratamiento)
            ids_candidatos = [c['id'] for c in candidatos]

            if not ids_candidatos:
                return jsonify({"status": "success", "data": []})

            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()

            placeholders = ",".join("?" * len(ids_candidatos))
            sql = f"""
                SELECT c.hora_inicio, c.hora_fin, c.id_odontologo FROM tblcita c
                LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                WHERE c.fecha = ?
                AND (a.id_estado IS NULL OR a.id_estado != 2)
                AND c.id_odontologo IN ({placeholders})
            """
            params = [fecha] + ids_candidatos
            if edit_id and edit_id not in ["null", "undefined", ""]:
                sql += " AND c.id_cita != ?"
                params.append(edit_id)

            cursor.execute(sql, params)
            citas_del_dia = cursor.fetchall()

            # ── NUEVO: citas del paciente en esa fecha (sin importar el tratamiento) ──
            sql_paciente = """
                SELECT c.hora_inicio, c.hora_fin FROM tblcita c
                LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                WHERE c.fecha = ?
                AND c.id_usuario = ?
                AND (a.id_estado IS NULL OR a.id_estado != 2)
            """
            params_paciente = [fecha, id_usuario_sesion]
            if edit_id and edit_id not in ["null", "undefined", ""]:
                sql_paciente += " AND c.id_cita != ?"
                params_paciente.append(edit_id)

            cursor.execute(sql_paciente, params_paciente)
            citas_paciente = cursor.fetchall()

            HORARIOS_MAESTROS_BACKEND = [
                "08:00 AM", "08:45 AM", "09:30 AM", "10:15 AM", "11:00 AM", "11:45 AM",
                "02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM"
            ]

            ocupadas = []
            for hora_str in HORARIOS_MAESTROS_BACKEND:
                slot_inicio = datetime.strptime(hora_str, "%I:%M %p")

                # ── NUEVO: ¿el paciente ya tiene algo a esta hora? ──
                paciente_ocupado = False
                for fila in citas_paciente:
                    inicio = datetime.strptime(fila['hora_inicio'], "%H:%M:%S")
                    fin    = datetime.strptime(fila['hora_fin'],    "%H:%M:%S")
                    if inicio <= slot_inicio < fin:
                        paciente_ocupado = True
                        break

                if paciente_ocupado:
                    ocupadas.append(hora_str)
                    continue

                # Lógica original: bloquear solo si TODOS los doctores están ocupados
                doctores_ocupados_este_slot = set()
                for fila in citas_del_dia:
                    inicio = datetime.strptime(fila['hora_inicio'], "%H:%M:%S")
                    fin    = datetime.strptime(fila['hora_fin'],    "%H:%M:%S")
                    if inicio <= slot_inicio < fin:
                        doctores_ocupados_este_slot.add(fila['id_odontologo'])

                if len(doctores_ocupados_este_slot) >= len(ids_candidatos):
                    ocupadas.append(hora_str)

            return jsonify({"status": "success", "data": ocupadas})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion: conexion.close()

    # ── Citas del usuario logueado ────────────────────────────────────────
    elif action == 'get_citas_usuario':
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT c.id_cita as id, c.fecha, c.hora_inicio as hora,
                       c.id_odontologo, c.id_sala,
                       COALESCE(c.tratamiento, 'Revisión general') AS tratamiento,
                       COALESCE(a.id_estado, 1)                    AS id_estado,
                       COALESCE(e.nombre_estado, 'programada')     AS nombre_estado
                FROM tblcita c
                LEFT JOIN tblagenda      a ON c.id_cita   = a.id_cita
                LEFT JOIN tblestadocita  e ON a.id_estado = e.id_estado
                WHERE c.id_usuario = ?
                ORDER BY c.fecha DESC, c.hora_inicio DESC
            """, [id_usuario_sesion])

            ETIQUETAS = {
                "programada":   ("🟢", "#10b981"),
                "reprogramada": ("🔵", "#0052FF"),
                "completada":   ("✅", "#6366f1"),
                "cancelada":    ("🔴", "#ef4444"),
                "no_asistio":   ("⚠️",  "#f59e0b"),
            }

            res = []
            for c in cursor.fetchall():
                hora_obj    = datetime.strptime(c['hora'], "%H:%M:%S")
                nombre_trat = c['tratamiento']
                estado_key  = c['nombre_estado'].lower().replace(" ", "_")
                icono_estado, color_estado = ETIQUETAS.get(estado_key, ("🟢", "#10b981"))
                res.append({
                    "id":               c['id'],
                    "tratamiento":      nombre_trat,
                    "tratamientoIcono": icono_para_tratamiento(nombre_trat),
                    "doctor":           obtener_nombre_doctor_js(c['id_odontologo']),
                    "fecha":            c['fecha'],
                    "hora":             hora_obj.strftime("%I:%M %p"),
                    "id_estado":        c['id_estado'],
                    "nombre_estado":    c['nombre_estado'],
                    "icono_estado":     icono_estado,
                    "color_estado":     color_estado,
                })
            return jsonify({"status": "success", "data": res})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion: conexion.close()

    # ── Una cita específica (para edición/reprogramación) ─────────────────
    elif action == 'get_una_cita':
        id_cita  = request.args.get('id_cita', '')
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT *, COALESCE(tratamiento, 'Revisión general') AS tratamiento
                FROM tblcita WHERE id_cita = ?
            """, [id_cita])
            cita = cursor.fetchone()

            if cita:
                nombre_trat = cita['tratamiento']
                hora_obj    = datetime.strptime(cita['hora_inicio'], "%H:%M:%S")
                return jsonify({
                    "status": "success",
                    "data": {
                        "id":               cita['id_cita'],
                        "doctor":           obtener_nombre_doctor_js(cita['id_odontologo']),
                        "doctor_id":        cita['id_odontologo'],
                        "fecha":            cita['fecha'],
                        "hora":             hora_obj.strftime("%I:%M %p"),
                        "tratamiento":      nombre_trat,
                        "tratamientoIcono": icono_para_tratamiento(nombre_trat)
                    }
                })
            return jsonify({"status": "error", "message": "Cita no encontrada."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion: conexion.close()

    return jsonify({"status": "error", "message": "Acción no válida."})


# =========================================================================
# ─── ACCIONES POST
# =========================================================================

@agenda_blueprint.route('/agenda_cliente', methods=['POST'])
def acciones_post():
    id_usuario_sesion = session.get('id_usuario', 3)
    action            = request.args.get('action', '')
    input_data        = request.get_json() or {}

    if not input_data and not request.form:
        return jsonify({"status": "error", "message": "Datos no válidos."})
    if not input_data:
        input_data = request.form

    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()

        # ── Cancelar cita ─────────────────────────────────────────────────
        if action == 'cancelar_cita':
            id_cita = input_data.get('id_cita')
            motivo  = input_data.get('motivo_cancelacion', '').strip()

            if not id_cita:
                return jsonify({"status": "error", "message": "ID de cita requerido."})
            if not motivo:
                return jsonify({"status": "error", "message": "Debes indicar el motivo de cancelación."})

            cursor.execute("SELECT COUNT(*) FROM tblagenda WHERE id_cita = ?", [id_cita])
            exists = cursor.fetchone()[0]
            if exists > 0:
                cursor.execute(
                    "UPDATE tblagenda SET id_estado = 2, motivo_cancelacion = ? WHERE id_cita = ?",
                    [motivo, id_cita]
                )
            else:
                cursor.execute(
                    "INSERT INTO tblagenda (id_cita, id_estado, motivo_cancelacion) VALUES (?, 2, ?)",
                    [id_cita, motivo]
                )

            conexion.commit()
            return jsonify({"status": "success", "message": "Cita cancelada con éxito."})

        # ── Crear / Reprogramar cita ──────────────────────────────────────
        else:
            edit_id        = input_data.get('edit_id')
            fecha          = input_data.get('fecha', '')
            hora_raw       = input_data.get('hora', '')
            tratamiento_js = input_data.get('tratamiento', 'Revisión general')

            if not fecha or not hora_raw:
                return jsonify({"status": "error", "message": "Fecha y hora requeridas."})

            hora_obj    = datetime.strptime(hora_raw, "%I:%M %p")
            hora_inicio = hora_obj.strftime("%H:%M:%S")

            # Duración según tratamiento
            nombre_lower = tratamiento_js.lower().strip()
            if nombre_lower == "ortodoncia":                               minutos = 60
            elif nombre_lower in ["blanqueamiento", "endodoncia"]:         minutos = 90
            elif nombre_lower == "cirugía oral":                           minutos = 120
            elif nombre_lower == "revisión general":                       minutos = 30
            else:                                                          minutos = 45  # Limpieza dental

            hora_fin = (hora_obj + timedelta(minutes=minutos)).strftime("%H:%M:%S")

            # ── Validar que el paciente no tenga otra cita solapada ───────
            # Usa hora_inicio y hora_fin ya calculadas con la duración real
            # del servicio, así una Cirugía Oral de 120 min bloquea los
            # slots que caigan dentro de ese lapso, no solo el de inicio.
            excluir = edit_id if (edit_id and edit_id not in ["null", "undefined", ""]) else None

            sql_choque_paciente = """
                SELECT COUNT(*) FROM tblcita c
                LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                WHERE c.fecha      = ?
                  AND c.id_usuario = ?
                  AND (a.id_estado IS NULL OR a.id_estado != 2)
                  AND c.hora_inicio < ?
                  AND c.hora_fin    > ?
            """
            params_choque = [fecha, id_usuario_sesion, hora_fin, hora_inicio]
            if excluir:
                sql_choque_paciente += " AND c.id_cita != ?"
                params_choque.append(excluir)

            cursor.execute(sql_choque_paciente, params_choque)
            if cursor.fetchone()[0] > 0:
                return jsonify({
                    "status":  "error",
                    "message": "Ya tienes una cita programada en ese horario."
                })

            # ── Buscar doctor disponible ──────────────────────────────────
            candidatos = obtener_odontologos_por_tratamiento(tratamiento_js)
            if not candidatos:
                return jsonify({"status": "error", "message": "No hay especialistas para este tratamiento."})

            asignacion = elegir_doctor_disponible(
                candidatos, fecha, hora_inicio, hora_fin, excluir_id_cita=excluir
            )

            if asignacion is None:
                return jsonify({
                    "status":  "error",
                    "message": "Todos los especialistas de este servicio están ocupados en ese horario."
                })

            id_odontologo = asignacion["id_odontologo"]
            id_sala       = asignacion["id_sala"]

            if excluir:
                cursor.execute("""
                    UPDATE tblcita
                    SET fecha = ?, hora_inicio = ?, hora_fin = ?,
                        id_odontologo = ?, id_sala = ?, tratamiento = ?
                    WHERE id_cita = ?
                """, [fecha, hora_inicio, hora_fin, id_odontologo, id_sala, tratamiento_js, excluir])
                cursor.execute(
                    "UPDATE tblagenda SET id_estado = 3 WHERE id_cita = ?", [excluir]
                )
            else:
                cursor.execute("""
                    INSERT INTO tblcita
                        (fecha, hora_inicio, hora_fin, id_usuario, id_odontologo, id_sala, tratamiento)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [fecha, hora_inicio, hora_fin, id_usuario_sesion,
                      id_odontologo, id_sala, tratamiento_js])
                nuevo_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 1)", [nuevo_id]
                )

            conexion.commit()
            return jsonify({
                "status": "success",
                "message": "Completado",
                "doctor_asignado": obtener_nombre_doctor_js(id_odontologo)
            })

    except Exception as e:
        if conexion: conexion.rollback()
        return jsonify({"status": "error", "message": f"Error de DB: {str(e)}"})
    finally:
        if conexion: conexion.close()