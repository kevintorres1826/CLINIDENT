import os
import sys
import sqlite3
from flask import Blueprint, request, jsonify, session

# Solución de portabilidad absoluta: Encuentra la ruta raíz del .exe o script principal
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    # Sube un nivel si este archivo está metido dentro de la subcarpeta 'login/'
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta unificada a la base de datos real
RUTA_BD = os.path.join(ruta_base, "clinident.db")

# Creamos el Blueprint para esta carpetita
login_blueprint = Blueprint('login_blueprint', __name__)

@login_blueprint.route('/login', methods=['POST'])
def ejecutar_login():
    """
    Controlador de inicio de sesión individual.
    Mantiene la lógica exacta de tu login.php original pero adaptado a SQLite portable.
    """
    # Capturar parámetros (Soporta formularios tradicionales POST y Fetch/JSON)
    if request.is_json:
        datos = request.get_json() or {}
        correo_input = datos.get('usuario', '').strip()
        pass_input = datos.get('contrasena', '')
    else:
        correo_input = request.form.get('usuario', '').strip()
        pass_input = request.form.get('contrasena', '')

    if not correo_input or not pass_input:
        return jsonify({'status': 'error', 'msg': '⚠️ Por favor escribe tu correo y contraseña.'})

    conexion = None
    try:
        # Nos conectamos directamente a la ruta unificada de la base de datos
        conexion = sqlite3.connect(RUTA_BD)
        
        # 🚀 CONFIGURACIÓN CLAVE: Mapea las columnas para poder llamarlas por su nombre usuario['contrasena']
        conexion.row_factory = sqlite3.Row 
        
        cursor = conexion.cursor()

        # Buscamos al usuario únicamente por su correo electrónico
        sql_user = """
            SELECT id_usuario, id_rol, nombre, apellido, contrasena, estado 
            FROM tblusuario 
            WHERE correo = ?
        """
        cursor.execute(sql_user, [correo_input])
        usuario = cursor.fetchone()

        if usuario:
            # Ahora sí puedes acceder de forma segura usando las claves de texto 🎉
            if pass_input == usuario['contrasena']:
                if usuario['estado'] != 'Activo':
                    return jsonify({'status': 'error', 'msg': '⚠️ Tu usuario clínico se encuentra inactivo.'})

                # Guardamos las variables de sesión
                session['id_usuario'] = usuario['id_usuario']
                session['id_rol'] = usuario['id_rol']
                session['nombre'] = usuario['nombre']
                session['nombre_usuario'] = usuario['nombre'] # Compatibilidad de la agenda
                session['apellido'] = usuario['apellido']
                session['correo'] = correo_input
                
                # Mapeo de rutas dinámicas según el rol
                rutas = {
                    1: '/web/odontologo/panel_medico.html',
                    2: '/web/odontologo/panel_medico.html',
                    3: '/web/recepcionista/panel_rec.html',
                    4: '/web/agenda_cliente/index.html'
                }
                
                redireccion = rutas.get(usuario['id_rol'], '../agenda_cliente/index.html')
                
                return jsonify({
                    'status': 'success',
                    'msg': '¡Ingreso correcto!',
                    'redirect': redireccion,
                    'nombre': usuario['nombre'],
                    'id_rol': usuario['id_rol'] 
                })
            else:
                return jsonify({'status': 'error', 'msg': '⚠️ Correo o contraseña incorrectos.'})
        else:
            return jsonify({'status': 'error', 'msg': '⚠️ Correo o contraseña incorrectos.'})

    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'msg': f'Error de lectura local: {str(e)}'})
        
    finally:
        if conexion:
            conexion.close()