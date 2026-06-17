

import os
import sys
import time
import sqlite3
from flask import Blueprint, request, jsonify, session
 
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
RUTA_BD = os.path.join(ruta_base, "clinident.db")
 
login_blueprint = Blueprint('login_blueprint', __name__)
 
 
@login_blueprint.route('/login', methods=['POST'])
def ejecutar_login():
    if request.is_json:
        datos = request.get_json() or {}
        correo_input = datos.get('usuario', '').strip()
        pass_input   = datos.get('contrasena', '')
    else:
        correo_input = request.form.get('usuario', '').strip()
        pass_input   = request.form.get('contrasena', '')
 
    if not correo_input or not pass_input:
        return jsonify({'status': 'error', 'msg': '⚠️ Por favor escribe tu correo y contraseña.'})
 
    # ── RATE LIMITING: verificar bloqueo activo ────────────────────────────
    ahora = int(time.time())
 
    if 'bloqueado_hasta' in session and ahora < session['bloqueado_hasta']:
        tiempo_restante = session['bloqueado_hasta'] - ahora
        return jsonify({
            'status':          'error',
            'msg':             f'⚠️ Demasiados intentos fallidos. Espera {tiempo_restante} segundos.',
            'bloqueado':       True,
            'tiempo_restante': tiempo_restante
        }), 429
    # ──────────────────────────────────────────────────────────────────────
 
    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()
 
        # Obtener usuario por correo
        cursor.execute("""
            SELECT id_usuario, nombre, apellido, contrasena, estado
            FROM tblusuario WHERE correo = ?
        """, [correo_input])
        usuario = cursor.fetchone()

        # ── GUARDIA 1: Usuario inactivo → bloqueo inmediato, sin contar intentos ──
        if usuario and usuario['estado'] != 'Activo':
            return jsonify({'status': 'error', 'msg': '⚠️ Tu usuario clínico se encuentra inactivo.'})
        # ────────────────────────────────────────────────────────────────────────
 
        # ── Credenciales incorrectas: contador de intentos ─────────────────
        if not usuario or pass_input != usuario['contrasena']:
            intentos = session.get('intentos_fallidos', 0) + 1
            session['intentos_fallidos'] = intentos
 
            if intentos >= 3:
                session['bloqueado_hasta']  = ahora + 30
                session['intentos_fallidos'] = 0
                return jsonify({
                    'status':          'error',
                    'msg':             '⚠️ Has superado los 3 intentos. Ingreso bloqueado por 30 segundos.',
                    'bloqueado':       True,
                    'tiempo_restante': 30
                }), 429
 
            restantes = 3 - intentos
            return jsonify({
                'status': 'error',
                'msg':    f'⚠️ Correo o contraseña incorrectos. Intentos restantes: {restantes}.'
            })
        # ──────────────────────────────────────────────────────────────────
 
        # ── ÉXITO: limpiar contadores ──────────────────────────────────────
        session.pop('intentos_fallidos', None)
        session.pop('bloqueado_hasta',   None)
        # ──────────────────────────────────────────────────────────────────
 
        # Obtener TODOS los roles del usuario desde tblusuario_rol
        cursor.execute("""
            SELECT id_rol FROM tblusuario_rol
            WHERE id_usuario = ?
            ORDER BY id_rol ASC
        """, [usuario['id_usuario']])
        roles = [r['id_rol'] for r in cursor.fetchall()]
 
        # Fallback: si la tabla aún no existe o está vacía, leer id_rol legacy
        if not roles:
            cursor.execute("SELECT id_rol FROM tblusuario WHERE id_usuario = ?", [usuario['id_usuario']])
            fila = cursor.fetchone()
            if fila and fila['id_rol']:
                roles = [fila['id_rol']]
 
        if not roles:
            return jsonify({'status': 'error', 'msg': '⚠️ El usuario no tiene ningún rol asignado.'})
 
        # Guardar sesión
        session['id_usuario']     = usuario['id_usuario']
        session['nombre']         = usuario['nombre']
        session['nombre_usuario'] = usuario['nombre']
        session['apellido']       = usuario['apellido']
        session['correo']         = correo_input
        session['roles']          = roles      # lista completa
        session['id_rol']         = roles[0]   # rol principal
 
        # ── Lógica de redirección ──────────────────────────────────────────
        # El admin (1) no tiene panel propio: usa el panel del siguiente rol.
        # Orden de prioridad de destino: 2 → 3 → 4
        # Ejemplos:
        #   roles [1, 2] → panel médico   (odontólogo)
        #   roles [1, 3] → panel recepción
        #   roles [1, 4] → agenda cliente
        #   roles [1]    → agenda cliente  (admin puro)
        #   roles [2]    → panel médico
        #   roles [3]    → panel recepción
        #   roles [4]    → agenda cliente
 
        rutas = {
            2: '/web/odontologo/panel_medico.html',
            3: '/web/recepcionista/panel_rec.html',
            4: '/web/agenda_cliente/index.html'
        }
 
        # Buscar el primer rol con panel propio, saltando el rol admin (1)
        rol_destino = next((r for r in sorted(roles) if r != 1), None)
 
        # Si solo tiene rol 1 (admin puro sin otro rol asignado) → agenda cliente
        if rol_destino is None:
            rol_destino = 4
 
        redireccion = rutas.get(rol_destino, '/web/agenda_cliente/index.html')
 
        return jsonify({
            'status':   'success',
            'msg':      '¡Ingreso correcto!',
            'redirect': redireccion,
            'nombre':   usuario['nombre'],
            'roles':    roles,
            'id_rol':   rol_destino
        })
 
    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'msg': f'Error de base de datos: {str(e)}'})
    finally:
        if conexion:
            conexion.close()
 