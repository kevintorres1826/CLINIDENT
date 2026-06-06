import os
import sys
import sqlite3
from flask import Blueprint, request, jsonify, session

# Mantenemos la lógica de rutas para que funcione tanto en .exe como en desarrollo
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_BD = os.path.join(ruta_base, "clinident.db")

agenda_recepcion_blueprint = Blueprint('agenda_recepcion_blueprint', __name__)

# 1. RUTA: OBTENER TODOS LOS PACIENTES (Para el selector desplegable)
@agenda_recepcion_blueprint.route('/pacientes', methods=['GET'])
def obtener_pacientes():
    if session.get('id_rol') not in [1, 3]:
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    
    # Traemos a todos los pacientes (id_rol = 4) ordenados alfabéticamente
    cursor.execute("SELECT id_usuario, nombre, apellido, correo FROM tblusuario WHERE id_rol = 4 ORDER BY nombre ASC")
    pacientes = [dict(row) for row in cursor.fetchall()]
    conexion.close()

    return jsonify({"status": "success", "data": pacientes})


# 2. RUTA: AGENDAR CITA
@agenda_recepcion_blueprint.route('/agendar', methods=['POST'])
def agendar_cita_recepcionista():
    if session.get('id_rol') not in [1, 3]:
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    data = request.get_json()
    id_usuario_existente = data.get('id_usuario_existente')
    nombre = data.get('nombre', '').strip()
    apellido = data.get('apellido', '').strip()
    id_odontologo = data.get('id_odontologo')
    fecha = data.get('fecha')
    hora = data.get('hora')

    # Validación básica
    if not all([id_odontologo, fecha, hora]):
        return jsonify({"status": "error", "message": "Faltan campos obligatorios."}), 400

    hora_inicio = f"{hora}:00"
    # Lógica simple de fin de cita (1 hora después)
    h, m = map(int, hora.split(':'))
    hora_fin = f"{str(h+1).zfill(2)}:{str(m).zfill(2)}:00"

    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    
    try:
        # Si no existe usuario, se crea automáticamente
        if not id_usuario_existente:
            if not nombre or not apellido:
                return jsonify({"status": "error", "message": "Nombre y apellido son obligatorios para un paciente nuevo."}), 400
                
            correo_temp = f"{nombre.lower()}.{apellido.lower()}@clinident.temp"
            cursor.execute(
                "INSERT INTO tblusuario (nombre, apellido, correo, contrasena, id_rol, estado) VALUES (?, ?, ?, ?, 4, 'Activo')",
                (nombre, apellido, correo_temp, "clinident123")
            )
            id_usuario_paciente = cursor.lastrowid
        else:
            id_usuario_paciente = id_usuario_existente

        # Validar colisiones de horario
        check_sql = """
            SELECT COUNT(*) FROM tblcita 
            WHERE fecha = ? AND id_odontologo = ? 
            AND ((hora_inicio <= ? AND hora_fin > ?) OR (hora_inicio < ? AND hora_fin >= ?) OR (? <= hora_inicio AND ? > hora_inicio))
        """
        cursor.execute(check_sql, [fecha, id_odontologo, hora_inicio, hora_inicio, hora_fin, hora_fin, hora_inicio, hora_fin])
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "error", "message": "El especialista ya tiene una cita en ese horario."})

        # Insertar cita
        cursor.execute(
            "INSERT INTO tblcita (fecha, hora_inicio, hora_fin, id_usuario, id_odontologo, id_sala) VALUES (?, ?, ?, ?, ?, 1)",
            (fecha, hora_inicio, hora_fin, id_usuario_paciente, id_odontologo)
        )
        id_cita = cursor.lastrowid
        cursor.execute("INSERT INTO tblagenda (id_cita, id_estado) VALUES (?, 1)", (id_cita,))
        
        conexion.commit()
        return jsonify({"status": "success", "message": "¡Cita registrada correctamente!"})
    except Exception as e:
        conexion.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conexion.close()