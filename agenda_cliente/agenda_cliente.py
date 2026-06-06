import os
import sys
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session

print("=== VERSION NUEVA agenda_cliente.py ===")
print("=== AGENDA CLIENTE CARGADO ===")

# Solución de portabilidad absoluta
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_BD = os.path.join(ruta_base, "clinident.db")

agenda_blueprint = Blueprint('agenda_blueprint', __name__)

def obtener_odontologos_disponibles():
    """Consulta la DB para traer odontólogos reales (rol 2)"""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, nombre, apellido FROM tblusuario WHERE id_rol = 2 AND estado = 'Activo'")
    odontologos = cursor.fetchall()
    conexion.close()
    return [{"id": o['id_usuario'], "nombre": f"Dr. {o['nombre']} {o['apellido']}"} for o in odontologos]

def obtener_sala_segun_tratamiento(tratamiento_name):
    """Asignación lógica de salas basada únicamente en el tratamiento"""
    if tratamiento_name == "Cirugía Oral": return 4
    if tratamiento_name == "Limpieza Dental": return 5
    if tratamiento_name == "Ortodoncia": return 3
    return 2 

def obtener_nombre_doctor_js(id_odontologo):
    """Devuelve la cadena formateada del nombre completo del especialista"""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, apellido FROM tblusuario WHERE id_usuario = ?", [id_odontologo])
    doc = cursor.fetchone()
    conexion.close()
    if doc:
        return f"Dr. {doc[0]} {doc[1]}"
    return "Especialista"

# =========================================================================
# ─── ACCIONES GET (CONSULTAS DE DATOS)
# =========================================================================

@agenda_blueprint.route('/agenda_cliente', methods=['GET'])
def acciones_get():
    id_usuario_sesion = session.get('id_usuario', 3)
    nombre_usuario_sesion = session.get('nombre_usuario', session.get('nombre', 'Paciente'))

    action = request.args.get('action', '')

    if action == 'get_sesion_usuario':
        return jsonify({
            "status": "success",
            "id": id_usuario_sesion,
            "nombre": nombre_usuario_sesion,
            "id_rol": session.get('id_rol')
        })

    elif action == 'get_odontologos':
        return jsonify({"status": "success", "data": obtener_odontologos_disponibles()})

    elif action == 'get_citas_ocupadas':
        fecha = request.args.get('fecha', '')
        doctor_id = request.args.get('doctor', '')
        edit_id = request.args.get('edit_id', '')

        if not fecha or not doctor_id:
            return jsonify({"status": "success", "data": []})

        conexion = None
        try:
            id_odontologo = int(doctor_id)
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()

            sql = """
            SELECT c.hora_inicio
            FROM tblcita c
            LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
            WHERE c.fecha = ?
              AND c.id_odontologo = ?
              AND (a.id_estado IS NULL OR a.id_estado != 2)
            """
            params = [fecha, id_odontologo]
            
            if edit_id and edit_id not in ["null", "undefined", ""]:
                sql += " AND c.id_cita != ?"
                params.append(edit_id)

            cursor.execute(sql, params)
            horas_db = cursor.fetchall()

            ocupadas = []
            for row in horas_db:
                hora_obj = datetime.strptime(row['hora_inicio'], "%H:%M:%S")
                ocupadas.append(hora_obj.strftime("%I:%M %p"))

            return jsonify({"status": "success", "data": ocupadas})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion:
                conexion.close()

    elif action == 'get_citas_usuario':
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()
            sql = """SELECT c.id_cita as id, c.fecha, c.hora_inicio as hora, c.id_odontologo, c.id_sala
                     FROM tblcita c
                     LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                     WHERE c.id_usuario = ? 
                       AND (a.id_estado IS NULL OR a.id_estado IN (1, 3))
                     ORDER BY c.fecha ASC, c.hora_inicio ASC"""
            
            cursor.execute(sql, [id_usuario_sesion])
            citas = cursor.fetchall()

            res = []
            for c in citas:
                tratamiento = "Limpieza Dental"
                icono = "🦷"

                if c['id_odontologo'] == 3:
                    tratamiento = "Ortodoncia"
                    icono = "😁"
                elif c['id_odontologo'] == 4:
                    if c['id_sala'] == 4:
                        tratamiento = "Cirugía Oral"
                        icono = "🔬"
                    else:
                        tratamiento = "Endodoncia"
                        icono = "💉"
                elif c['id_sala'] == 1:
                    tratamiento = "Revisión General"
                    icono = "🩺"

                hora_obj = datetime.strptime(c['hora'], "%H:%M:%S")

                res.append({
                    "id": c['id'],
                    "tratamiento": tratamiento,
                    "tratamientoIcono": icono,
                    "doctor": obtener_nombre_doctor_js(c['id_odontologo']),
                    "fecha": c['fecha'],
                    "hora": hora_obj.strftime("%I:%M %p")
                })

            return jsonify({"status": "success", "data": res})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion:
                conexion.close()

    elif action == 'get_una_cita':
        id_cita = request.args.get('id_cita', '')
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM tblcita WHERE id_cita = ?", [id_cita])
            cita = cursor.fetchone()

            if cita:
                tratamiento = "Limpieza Dental"
                icono = "🦷"
                if cita['id_odontologo'] == 3: tratamiento = "Ortodoncia"; icono = "😁"
                if cita['id_odontologo'] == 4: 
                    tratamiento = "Cirugía Oral" if cita['id_sala'] == 4 else "Endodoncia"
                    icono = "🔬" if cita['id_sala'] == 4 else "💉"

                hora_obj = datetime.strptime(cita['hora_inicio'], "%H:%M:%S")

                return jsonify({
                    "status": "success",
                    "data": {
                        "id": cita['id_cita'],
                        "doctor": obtener_nombre_doctor_js(cita['id_odontologo']),
                        "fecha": cita['fecha'],
                        "hora": hora_obj.strftime("%I:%M %p"),
                        "tratamiento": tratamiento,
                        "tratamientoIcono": icono
                    }
                })
            return jsonify({"status": "error", "message": "Cita no encontrada."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if conexion:
                conexion.close()

    return jsonify({"status": "error", "message": "Acción no válida."})


# =========================================================================
# ─── ACCIONES POST (ESCRITURA Y MODIFICACIONES)
# =========================================================================

@agenda_blueprint.route('/agenda_cliente', methods=['POST'])
def acciones_post():
    id_usuario_sesion = session.get('id_usuario', 3)
    action = request.args.get('action', '')
    
    input_data = request.get_json() or {}

    if not input_data and not request.form:
        return jsonify({"status": "error", "message": "Datos no válidos."})
        
    if not input_data:
        input_data = request.form

    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()

        if action == 'cancelar_cita':
            id_cita = input_data.get('id_cita')
            if not id_cita:
                return jsonify({"status": "error", "message": "ID de cita requerido."})

            cursor.execute("SELECT COUNT(*) FROM tblagenda WHERE id_cita = ?", [id_cita])
            exists = cursor.fetchone()[0]
            
            if exists > 0:
                cursor.execute("UPDATE tblagenda SET id_estado = 2 WHERE id_cita = ?", [id_cita])
            else:
                cursor.execute("INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 2)", [id_cita])
            
            conexion.commit()
            return jsonify({"status": "success", "message": "Cita cancelada con éxito."})

        else:
            edit_id = input_data.get('edit_id')
            fecha = input_data.get('fecha', '')
            hora_raw = input_data.get('hora', '')
            tratamiento_js = input_data.get('tratamiento', 'Limpieza Dental')

            if not fecha or not hora_raw:
                return jsonify({"status": "error", "message": "Fecha y hora requeridas."})

            hora_obj = datetime.strptime(hora_raw, "%I:%M %p")
            hora_inicio = hora_obj.strftime("%H:%M:%S")
            
            minutos = 45
            if tratamiento_js == "Ortodoncia": minutos = 60
            if tratamiento_js in ["Blanqueamiento", "Endodoncia"]: minutos = 90
            if tratamiento_js == "Cirugía Oral": minutos = 120
            if tratamiento_js == "Revisión General": minutos = 30

            hora_fin_obj = hora_obj + timedelta(minutes=minutos)
            hora_fin = hora_fin_obj.strftime("%H:%M:%S")

            try:
                id_odontologo = int(input_data.get('doctor_id'))
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Especialista seleccionado inválido."})

            id_sala = obtener_sala_segun_tratamiento(tratamiento_js)

            check_sql = """SELECT COUNT(*) FROM tblcita c
                           LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                           WHERE c.fecha = ? 
                             AND (a.id_estado IS NULL OR a.id_estado != 2)
                             AND (c.id_odontologo = ? OR c.id_sala = ?)
                             AND ((c.hora_inicio <= ? AND c.hora_fin > ?)
                                  OR (c.hora_inicio < ? AND c.hora_fin >= ?))"""
            
            params = [fecha, id_odontologo, id_sala, hora_inicio, hora_inicio, hora_fin, hora_fin]
            if edit_id and edit_id not in ["null", "undefined", ""]:
                check_sql += " AND c.id_cita != ?"
                params.append(edit_id)

            cursor.execute(check_sql, params)
            colisiones = cursor.fetchone()[0]
            
            if colisiones > 0:
                return jsonify({"status": "error", "message": "El especialista o consultorio ya está reservado en este horario."})

            if edit_id and edit_id not in ["null", "undefined", ""]:
                cursor.execute("""UPDATE tblcita 
                                  SET fecha = ?, hora_inicio = ?, hora_fin = ?, id_odontologo = ?, id_sala = ? 
                                  WHERE id_cita = ?""", [fecha, hora_inicio, hora_fin, id_odontologo, id_sala, edit_id])
                cursor.execute("UPDATE tblagenda SET id_estado = 3 WHERE id_cita = ?", [edit_id])
            else:
                cursor.execute("""INSERT INTO tblcita (fecha, hora_inicio, hora_fin, id_usuario, id_odontologo, id_sala) 
                      VALUES (?, ?, ?, ?, ?, ?)""", 
                   [fecha, hora_inicio, hora_fin, id_usuario_sesion, id_odontologo, id_sala])
                
                nuevo_id = cursor.lastrowid
                cursor.execute("INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 1)", [nuevo_id])

            conexion.commit()
            return jsonify({"status": "success", "message": "Completado"})

    except Exception as e:
        if conexion:
            conexion.rollback()
        return jsonify({"status": "error", "message": f"Error de DB: {str(e)}"})
    finally:
        if conexion:
            conexion.close()