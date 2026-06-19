import os
import sqlite3
from flask import Blueprint, jsonify, session

historial_citas_blueprint = Blueprint('historial_citas', __name__)

def get_db():
    from main import RUTA_BD
    return sqlite3.connect(RUTA_BD)

def _roles_sesion():
    return set(session.get('roles', [session.get('id_rol', 0)]))


# ── 1. GET /historial_citas/todas ────────────────────────────────────────────
@historial_citas_blueprint.route('/todas', methods=['GET'])
def obtener_todas_citas():
    if 'id_usuario' not in session:
        return jsonify({"status": "error", "message": "No autorizado"}), 401

    conn = get_db()
    try:
        roles      = _roles_sesion()
        id_usuario = session.get('id_usuario')

        filtro_usuario = ""
        parametros     = []

        if not roles & {1, 2, 3}:
            filtro_usuario = "WHERE c.id_usuario = ?"
            parametros.append(id_usuario)

        query = f"""
            SELECT
                c.id_cita,
                u_pac.nombre || ' ' || u_pac.apellido AS paciente,
                u_od.nombre  || ' ' || u_od.apellido  AS odontologo,
                s.nombre_sala AS sala,
                c.fecha,
                c.hora_inicio || ' - ' || c.hora_fin AS horario,
                COALESCE(e.nombre_estado, 'programada') AS estado,
                COALESCE(
                    (SELECT tt2.nombre
                    FROM tblhistorialclinico hc2
                    JOIN tbltratamiento     t2  ON t2.id_tratamiento = hc2.id_tratamiento
                    JOIN tbltipotratamiento tt2 ON tt2.id_tipo       = t2.id_tipo
                    WHERE hc2.id_cita = c.id_cita
                    LIMIT 1),
                    c.tratamiento,
                    '—'
                ) AS servicio,
                           
                CASE 
                    WHEN LOWER(COALESCE(e.nombre_estado, '')) IN ('cancelada', 'no_asistio') 
                    THEN '—'
                    ELSE COALESCE(
                        (SELECT CASE WHEN p2.pagado = 1 THEN 'Pagado' ELSE 'Pendiente' END
                        FROM tbltratamiento t3
                        JOIN tblfactura f2 ON f2.id_tratamiento = t3.id_tratamiento
                        JOIN tblpago    p2 ON p2.id_factura     = f2.id_factura
                        WHERE t3.id_cita = c.id_cita
                        LIMIT 1),
                        'Pendiente'
                    )
                END AS estado_pago
                                        
            FROM tblcita c
            JOIN tblusuario u_pac ON u_pac.id_usuario = c.id_usuario
            JOIN tblusuario u_od  ON u_od.id_usuario  = c.id_odontologo
            JOIN tblsala    s     ON s.id_sala         = c.id_sala
            LEFT JOIN tblagenda     a ON a.id_cita   = c.id_cita
            LEFT JOIN tblestadocita e ON e.id_estado = a.id_estado
            {filtro_usuario}
            ORDER BY c.fecha DESC, c.hora_inicio DESC
        """

        citas = conn.execute(query, tuple(parametros)).fetchall()

        resultado = []
        for fila in citas:
            resultado.append({
                "id_cita":     fila[0],
                "paciente":    fila[1],
                "odontologo":  fila[2],
                "sala":        fila[3],
                "fecha":       fila[4],
                "horario":     fila[5],
                "estado":      fila[6],
                "servicio":    fila[7],
                "estado_pago": fila[8],
            })

        return jsonify(resultado)

    except Exception as e:
        print(f"[ERROR] obtener_todas_citas: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()


# ── 2. GET /historial_citas/detalle/<id_cita> ────────────────────────────────
@historial_citas_blueprint.route('/detalle/<int:id_cita>', methods=['GET'])
def detalle_cita(id_cita):
    if 'id_usuario' not in session:
        return jsonify({"status": "error", "message": "No autorizado"}), 401

    conn = get_db()
    try:
        roles      = _roles_sesion()
        id_usuario = session.get('id_usuario')

        filtro_usuario = ""
        parametros     = [id_cita]

        if not roles & {1, 2, 3}:
            filtro_usuario = " AND c.id_usuario = ?"
            parametros.append(id_usuario)

        cita = conn.execute(f"""
            SELECT
                c.id_cita,
                c.fecha,
                c.hora_inicio,
                c.hora_fin,
                u_pac.nombre || ' ' || u_pac.apellido AS paciente,
                u_pac.telefono                         AS telefono_paciente,
                u_pac.correo                           AS correo_paciente,
                u_od.nombre  || ' ' || u_od.apellido  AS odontologo,
                u_od.telefono                          AS telefono_odontologo,
                s.nombre_sala                          AS sala,
                COALESCE(e.nombre_estado, 'sin estado') AS estado,
                COALESCE(e.descripcion, '—')            AS estado_descripcion
            FROM tblcita c
            JOIN tblusuario    u_pac ON u_pac.id_usuario = c.id_usuario
            JOIN tblusuario    u_od  ON u_od.id_usuario  = c.id_odontologo
            JOIN tblsala       s     ON s.id_sala         = c.id_sala
            LEFT JOIN tblagenda     a ON a.id_cita    = c.id_cita
            LEFT JOIN tblestadocita e ON e.id_estado  = a.id_estado
            WHERE c.id_cita = ? {filtro_usuario}
        """, tuple(parametros)).fetchone()

        if not cita:
            return jsonify({"status": "error", "message": "Cita no encontrada"}), 404

        resultado = {
            "id_cita": cita[0], "fecha": cita[1], "hora_inicio": cita[2], "hora_fin": cita[3],
            "paciente": cita[4], "telefono_paciente": cita[5], "correo_paciente": cita[6],
            "odontologo": cita[7], "telefono_odontologo": cita[8], "sala": cita[9],
            "estado": cita[10], "estado_descripcion": cita[11]
        }

        # Historial clínico
        hc = conn.execute("""
            SELECT hc.id_historial_clinico, hc.observaciones, hc.fecha,
                   tt.nombre, tt.descripcion, t.diagnostico, t.valor,
                   u_od.nombre || ' ' || u_od.apellido
            FROM tblhistorialclinico hc
            JOIN tbltratamiento     t    ON t.id_tratamiento = hc.id_tratamiento
            JOIN tbltipotratamiento tt   ON tt.id_tipo        = t.id_tipo
            JOIN tblusuario         u_od ON u_od.id_usuario   = t.id_odontologo
            WHERE hc.id_cita = ?
        """, (id_cita,)).fetchall()

        resultado['historial_clinico'] = [{
            "id_historial_clinico": h[0], "observaciones": h[1], "fecha_registro": h[2],
            "tipo_tratamiento": h[3], "descripcion_tratamiento": h[4],
            "diagnostico": h[5], "valor_tratamiento": h[6], "odontologo_tratante": h[7]
        } for h in hc]

        # Registros clínicos (notas)
        try:
            rc = conn.execute("""
                SELECT rc.fecha, rc.notes, u_od.nombre || ' ' || u_od.apellido
                FROM tblregistroclinico rc
                JOIN tblhistorialclinico hc  ON hc.id_historial_clinico = rc.id_historial_clinico
                JOIN tblusuario          u_od ON u_od.id_usuario          = rc.id_odontologo
                WHERE hc.id_cita = ?
                ORDER BY rc.fecha
            """, (id_cita,)).fetchall()
            resultado['registros_clinicos'] = [{"fecha": r[0], "notas": r[1], "autor": r[2]} for r in rc]
        except Exception:
            resultado['registros_clinicos'] = []

        # Factura y pago
        try:
            factura = conn.execute("""
                SELECT f.id_factura, f.fecha_emision, t.valor, m.descripcion,
                       CASE p.pagado WHEN 1 THEN 'Pagado' ELSE 'Pendiente' END,
                       p.fecha_pago
                FROM tblhistorialclinico hc
                JOIN tbltratamiento  t ON t.id_tratamiento = hc.id_tratamiento
                JOIN tblfactura      f ON f.id_tratamiento = t.id_tratamiento
                JOIN tblpago         p ON p.id_factura     = f.id_factura
                JOIN tblmetodopago   m ON m.id_metodo      = p.id_metodo
                WHERE hc.id_cita = ?
                LIMIT 1
            """, (id_cita,)).fetchone()

            resultado['factura'] = {
                "id_factura": factura[0], "fecha_emision": factura[1], "monto": factura[2],
                "metodo_pago": factura[3], "estado_pago": factura[4], "fecha_pago": factura[5]
            } if factura else None
        except Exception:
            resultado['factura'] = None

        # Modificaciones
        try:
            mods = conn.execute("""
                SELECT fecha_modificacion, fecha_nueva
                FROM tblhistorialmodificaciones
                WHERE id_cita = ?
                ORDER BY fecha_modificacion
            """, (id_cita,)).fetchall()
            resultado['modificaciones'] = [{"fecha_modificacion": m[0], "fecha_nueva": m[1]} for m in mods]
        except Exception:
            resultado['modificaciones'] = []

        return jsonify(resultado)

    except Exception as e:
        print(f"[ERROR] detalle_cita: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()