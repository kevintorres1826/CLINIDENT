import os
import sys
import sqlite3
from flask import Blueprint, request, jsonify

# Solución de portabilidad absoluta: Encuentra la ruta raíz del .exe o script principal
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    # Sube un nivel si este archivo está metido dentro de una subcarpeta (como 'login/')
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta unificada a la base de datos real
RUTA_BD = os.path.join(ruta_base, "clinident.db")

# Creamos el Blueprint para el módulo de registro
registro_blueprint = Blueprint('registro_blueprint', __name__)

@registro_blueprint.route('/registro', methods=['POST'])
def ejecutar_registro():
    """
    Controlador para el auto-registro de nuevos pacientes.
    Equivalente exacto a tu archivo registro.php original.
    """
    if request.is_json:
        datos = request.get_json() or {}
        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        email = datos.get('email', '').strip()
        telefono = datos.get('telefono', '').strip()
        password = datos.get('password', '')
    else:
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        password = request.form.get('password', '')

    if not nombre or not apellido or not email or not password:
        return jsonify({'status': 'error', 'msg': 'Por favor completa todos los campos obligatorios.'})

    conexion = None
    try:
        # Nos conectamos directamente a la ruta unificada de la base de datos
        conexion = sqlite3.connect(RUTA_BD)
        
        # Mapea las columnas para poder llamarlas por su nombre
        conexion.row_factory = sqlite3.Row 
        
        cursor = conexion.cursor()

        # 1. Validar duplicados localmente
        sql_check = "SELECT id_usuario FROM tblusuario WHERE correo = ?"
        cursor.execute(sql_check, [email])
        if cursor.fetchone():
            return jsonify({'status': 'error', 'msg': 'El correo electrónico ya se encuentra registrado.'})

        id_rol_paciente = 4  # Por defecto todo autoregistro es un Paciente
        estado_activo = 'Activo'
        telefono_final = telefono if telefono else None

        # 2. Inserción compatible con SQLite
        sql_insert = """
            INSERT INTO tblusuario (id_rol, nombre, apellido, correo, telefono, contrasena, estado) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_insert, [
            id_rol_paciente, nombre, apellido, email, telefono_final, password, estado_activo
        ])
        conexion.commit() # Guarda el nuevo paciente de forma permanente en clinident.db
        
        return jsonify({'status': 'success', 'msg': 'Cuenta creada con éxito en el sistema local.'})

    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'msg': f'Error de lectura local: {str(e)}'})
    finally:
        # Garantiza el cierre de la conexión pase lo que pase
        if conexion:
            conexion.close()