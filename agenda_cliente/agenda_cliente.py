import os
import sys
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session

# Solución de portabilidad absoluta: Encuentra la ruta raíz del .exe o script principal
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    # Sube un nivel si este archivo está metido dentro de una subcarpeta (como 'agenda_cliente/')
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta unificada a la base de datos real
RUTA_BD = os.path.join(ruta_base, "clinident.db")

# Creamos el Blueprint para el módulo de agenda de clientes
agenda_blueprint = Blueprint('agenda_blueprint', __name__)

def obtener_id_odontologo_y_sala(doctor_name, tratamiento_name):
    """Mapea el string del Especialista de JS al ID real de la base de datos"""
    id_odontologo = 5  # Dr. Alberto Casas / Fernández
    id_sala = 2        # Consultorio 1

    if 'Marín' in doctor_name or 'William Alton' in doctor_name or 'Willy' in doctor_name:
        id_odontologo = 3  # Dr. William Alton / Elena Marín
        id_sala = 3        # Consultorio 2
    elif 'Ruiz' in doctor_name or 'Michael Phillips' in doctor_name or 'Mike' in doctor_name:
        id_odontologo = 4  # Dr. Michael Phillips / Camilo Ruiz
        if tratamiento_name == "Cirugía Oral":
            id_sala = 4    # Sala de Cirugía
        else:
            id_sala = 2    # Consultorio 1
    else:
        if tratamiento_name == "Limpieza Dental":
            id_sala = 5    # Sala de Limpieza
            
    return id_odontologo, id_sala

def obtener_nombre_doctor_js(id_odontologo):
    """Mapea los IDs internos de odontólogos a los nombres legibles por tu JS"""
    if id_odontologo == 3: return "Dr. William Alton (Ortodoncia)"
    if id_odontologo == 4: return "Dr. Michael Phillips (Cirugía)"
    return "Dr. Alberto Fernández (General)"

# =========================================================================
# ─── ACCIONES GET (CONSULTAS DE DATOS)
# =========================================================================

@agenda_blueprint.route('/agenda_cliente', methods=['GET'])
def acciones_get():
    # Detectar usuario logueado desde la sesión global de Flask (ID 3 por defecto si está vacío)
    id_usuario_sesion = session.get('id_usuario', 3)
    nombre_usuario_sesion = session.get('nombre_usuario', session.get('nombre', 'Paciente'))

    action = request.args.get('action', '')

    # NUEVA ACCIÓN: Devuelve los datos del usuario en sesión actual al JavaScript
    if action == 'get_sesion_usuario':
        return jsonify({
            "status": "success",
            "id": id_usuario_sesion,
            "nombre": nombre_usuario_sesion
        })

    # A. OBTENER HORARIOS OCUPADOS
    elif action == 'get_citas_ocupadas':
        fecha = request.args.get('fecha', '')
        doctor_name = request.args.get('doctor', '')
        edit_id = request.args.get('edit_id', '')

        if not fecha:
            return jsonify({"status": "success", "data": []})

        conexion = None
        try:
            id_odontologo, id_sala = obtener_id_odontologo_y_sala(doctor_name, '')
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row  # 🚀 Permitir acceso por nombre de columna
            
            cursor = conexion.cursor()

            sql = """SELECT c.hora_inicio 
                     FROM tblcita c 
                     LEFT JOIN tblagenda a ON c.id_cita = a.id_cita
                     WHERE c.fecha = ? 
                       AND (c.id_odontologo = ? OR c.id_sala = ?)
                       AND (a.id_estado IS NULL OR a.id_estado != 2)"""
            
            params = [fecha, id_odontologo, id_sala]
            
            if edit_id and edit_id not in ["null", "undefined", ""]:
                sql += " AND c.id_cita != ?"
                params.append(edit_id)

            cursor.execute(sql, params)
            horas_db = cursor.fetchall()

            # Formatear las horas devueltas de la DB ("08:00:00") al formato del JS ("08:00 AM")
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

    # B. HISTORIAL: LISTAR CITAS DEL PACIENTE LOGUEADO
    elif action == 'get_citas_usuario':
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row  # 🚀 Permitir acceso por nombre de columna
            
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

    # C. OBTENER DATOS DE UNA SOLA CITA
    elif action == 'get_una_cita':
        id_cita = request.args.get('id_cita', '')
        conexion = None
        try:
            conexion = sqlite3.connect(RUTA_BD)
            conexion.row_factory = sqlite3.Row  # 🚀 Permitir acceso por nombre de columna
            
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
    
    # Soporte para capturar el cuerpo json enviado mediante fetch()
    input_data = request.get_json() or {}

    if not input_data and not request.form:
        return jsonify({"status": "error", "message": "Datos no válidos."})
        
    if not input_data:
        input_data = request.form

    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        conexion.row_factory = sqlite3.Row  # 🚀 Permitir acceso por nombre de columna
        cursor = conexion.cursor()

        # D. CANCELAR CITA
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
            
            conexion.commit() # Guarda de forma segura
            return jsonify({"status": "success", "message": "Cita cancelada con éxito."}) # Corregido sintaxis de jsonify

        # E. GUARDAR O ACTUALIZAR CITA
        else:
            edit_id = input_data.get('edit_id')
            doctor_name = input_data.get('doctor', '')
            fecha = input_data.get('fecha', '')
            hora_raw = input_data.get('hora', '')
            tratamiento_js = input_data.get('tratamiento', 'Limpieza Dental')

            if not fecha or not hora_raw:
                return jsonify({"status": "error", "message": "Fecha y hora requeridas."})

            # Convertir hora del formato JS ("08:00 AM") a formato militar de base de datos ("08:00:00")
            hora_obj = datetime.strptime(hora_raw, "%I:%M %p")
            hora_inicio = hora_obj.strftime("%H:%M:%S")
            
            # Calcular duraciones exactas de manera dinámica
            minutos = 45
            if tratamiento_js == "Ortodoncia": minutos = 60
            if tratamiento_js in ["Blanqueamiento", "Endodoncia"]: minutos = 90
            if tratamiento_js == "Cirugía Oral": minutos = 120
            if tratamiento_js == "Revisión General": minutos = 30

            hora_fin_obj = hora_obj + timedelta(minutes=minutos)
            hora_fin = hora_fin_obj.strftime("%H:%M:%S")

            id_odontologo, id_sala = obtener_id_odontologo_y_sala(doctor_name, tratamiento_js)

            # Validar colisiones de tiempo (excluyendo la misma cita si es edición)
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
                # REPROGRAMAR CITA
                cursor.execute("""UPDATE tblcita 
                                  SET fecha = ?, hora_inicio = ?, hora_fin = ?, id_odontologo = ?, id_sala = ? 
                                  WHERE id_cita = ?""", [fecha, hora_inicio, hora_fin, id_odontologo, id_sala, edit_id])
                
                cursor.execute("UPDATE tblagenda SET id_estado = 3 WHERE id_cita = ?", [edit_id])
            else:
                # NUEVA CITA
                cursor.execute("""INSERT INTO tblcita (fecha, hora_inicio, hora_fin, id_usuario, id_odontologo, id_sala) 
                                  VALUES (?, ?, ?, ?, ?, ?)""", [fecha, hora_inicio, hora_fin, id_usuario_sesion, id_odontologo, id_sala])
                
                nuevo_id = cursor.lastrowid
                cursor.execute("INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 1)", [nuevo_id])

            conexion.commit() # Confirmación atómica limpia
            return jsonify({"status": "success", "message": "Completado"})

    except Exception as e:
        if conexion:
            conexion.rollback() # Si algo falla deshace los cambios evitando registros corruptos
        return jsonify({"status": "error", "message": f"Error de DB: {str(e)}"})
    finally:
        if conexion:
            conexion.close()