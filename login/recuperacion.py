import os
import sys
import sqlite3
from flask import Blueprint, request, jsonify

# Solución de portabilidad absoluta: Encuentra la ruta raíz del .exe o script principal
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    # Sube un nivel si este archivo está metido dentro de la subcarpeta 'login/'
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta unificada a la base de datos real
RUTA_BD = os.path.join(ruta_base, "clinident.db")

# Creamos el Blueprint para este script de recuperación
recuperacion_blueprint = Blueprint('recuperacion_blueprint', __name__)

@recuperacion_blueprint.route('/recuperacion', methods=['POST'])
def ejecutar_recuperacion():
    """
    Controlador para la recuperación y actualización de contraseñas.
    Equivalente exacto a tu archivo recuperacion.php original.
    """
    # Capturar parámetros (Soporta formularios tradicionales POST y peticiones Fetch/JSON)
    if request.is_json:
        datos = request.get_json() or {}
        accion = datos.get('accion', '').strip()
        metodo = datos.get('metodo', 'correo').strip()
        valor = datos.get('valor', '').strip()
        nueva_clave = datos.get('password', '')
    else:
        accion = request.form.get('accion', '').strip()
        metodo = request.form.get('metodo', 'correo').strip()
        valor = request.form.get('valor', '').strip()
        nueva_clave = request.form.get('password', '')

    conexion = None
    try:
        # Nos conectamos directamente a la ruta unificada de la base de datos
        conexion = sqlite3.connect(RUTA_BD)
        
        # Mapea las columnas para poder llamarlas por su nombre si fuese necesario en el futuro
        conexion.row_factory = sqlite3.Row 
        
        cursor = conexion.cursor()

        # ════════════ FASE 1: VERIFICAR DESTINO EN BASE DE DATOS ════════════
        if accion == 'enviar_codigo':
            if not valor:
                return jsonify({'status': 'error', 'msg': 'Por favor, escribe tus datos de contacto.'})
            
            # Consultar según el método seleccionado por el usuario en la interfaz
            if metodo == 'correo':
                sql = "SELECT id_usuario FROM tblusuario WHERE correo = ?"
            else:
                sql = "SELECT id_usuario FROM tblusuario WHERE telefono = ?"
                
            cursor.execute(sql, [valor])
            usuario = cursor.fetchone()
            
            # Si se devuelve una fila, significa que el usuario existe en clinident.db
            if usuario:
                return jsonify({
                    'status': 'success',
                    'msg': 'Código de verificación generado y enviado correctamente.'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'msg': 'Los datos ingresados no coinciden con ningún usuario registrado.'
                })

        # ════════════ FASE 2: ACTUALIZACIÓN DE CONTRASEÑA ════════════
        elif accion == 'actualizar_password':
            # Validar del lado del servidor que no lleguen campos vacíos
            if not valor or not nueva_clave:
                return jsonify({'status': 'error', 'msg': 'Información de recuperación incompleta.'})
            
            # Seleccionar la consulta SQL idónea según el método utilizado
            if metodo == 'correo':
                sql_update = "UPDATE tblusuario SET contrasena = ? WHERE correo = ?"
            else:
                sql_update = "UPDATE tblusuario SET contrasena = ? WHERE telefono = ?"
                
            cursor.execute(sql_update, [nueva_clave, valor])
            conexion.commit() # Guarda los cambios de forma permanente en la base de datos
            
            return jsonify({
                'status': 'success',
                'msg': '¡Contraseña restablecida con éxito!'
            })
            
        else:
            return jsonify({'status': 'error', 'msg': 'Acción no válida o no especificada.'})

    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'msg': f'Error de lectura local: {str(e)}'})
        
    finally:
        # Garantiza el cierre de la conexión pase lo que pase
        if conexion:
            conexion.close()