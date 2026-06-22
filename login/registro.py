
import re
import os
import sys
import sqlite3
 
from flask import Blueprint, request, jsonify, session
 
if getattr(sys, 'frozen', False):
    ruta_base = os.path.dirname(sys.executable)
else:
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
RUTA_BD = os.path.join(ruta_base, "clinident.db")
 
registro_blueprint = Blueprint('registro_blueprint', __name__)
 
# Contraseñas temporales que asignaba el sistema antiguo al crear pacientes físicos.
# Un usuario con alguna de estas claves se trata igual que si no tuviera contraseña.
CLAVES_TEMPORALES = {'clinident123', 'TempPass101', 'TempPass102', 'TempPass103',
                     'TempPass104', 'TempPass105', 'TempPass106', 'TempPass107',
                     'TempPass108', 'TempPass109', 'TempPass110', ''}
 
# Código fijo de verificación (entorno de pruebas SENA).
CODIGO_VALIDO = 'SENA4'
 
 
def _es_sin_cuenta(usuario):
    """
    Devuelve True si el registro no tiene una cuenta web real:
      - contraseña nula, vacía o es una de las claves temporales del sistema
      - Y el correo es nulo, vacío o termina en @clinident.temp
    """
    clave  = (usuario['contrasena'] or '').strip()
    correo = (usuario['correo']     or '').strip().lower()
    clave_temporal  = clave  in CLAVES_TEMPORALES
    correo_temporal = not correo or correo.endswith('@clinident.temp')
    return clave_temporal or correo_temporal   # basta con UNO de los dos
 
 
@registro_blueprint.route('/registro', methods=['POST'])
def ejecutar_registro():
    """
    Valida los datos de registro y los deja pendientes en sesión.
    IMPORTANTE: este endpoint NO escribe nada en la base de datos.
    El INSERT/UPDATE real solo ocurre en /verificar, una vez que el
    código de confirmación es correcto.
 
    Orden de búsqueda para detectar un alta física previa:
      1. Por correo exacto (no .temp)
      2. Por teléfono exacto          ← más confiable
      3. Por nombre + apellido        ← fallback
 
    Escenarios:
      A) Correo real encontrado CON cuenta real  → error, ya tiene cuenta.
      B) Coincidencia SIN cuenta real            → se marca para UPDATE al verificar.
      C) Nada coincide                           → se marca para INSERT al verificar.
    """
    if request.is_json:
        datos     = request.get_json() or {}
        nombre    = datos.get('nombre',    '').strip()
        apellido  = datos.get('apellido',  '').strip()
        email     = datos.get('email',     '').strip()
        telefono  = datos.get('telefono',  '').strip()
        password  = datos.get('password',  '')
        confirmar = datos.get('confirmar', '')
    else:
        nombre    = request.form.get('nombre',    '').strip()
        apellido  = request.form.get('apellido',  '').strip()
        email     = request.form.get('email',     '').strip()
        telefono  = request.form.get('telefono',  '').strip()
        password  = request.form.get('password',  '')
        confirmar = request.form.get('confirmar', '')
 
    if not nombre or not apellido or not email or not password:
        return jsonify({'status': 'error', 'msg': 'Por favor completa todos los campos obligatorios.'})
 
    if not telefono:
        return jsonify({'status': 'error', 'msg': '⚠️ El celular es obligatorio.'})
 
    if not re.fullmatch(r'\d{10}', telefono):
        return jsonify({'status': 'error', 'msg': '⚠️ El celular debe tener exactamente 10 dígitos numéricos.'})
 
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        return jsonify({'status': 'error', 'msg': '⚠️ El correo no tiene un formato válido.'})
 
    if password != confirmar:
        return jsonify({'status': 'error', 'msg': '⚠️ Las contraseñas no coinciden. Verifícalas e intenta de nuevo.'})
 
    # ── Validación de Contraseña Segura ────────────────────────────────────────
 
    # 1. Valida el tamaño
    if len(password) < 8:
        return jsonify({'status': 'error', 'msg': '⚠️ La contraseña falló: Debe tener al menos 8 caracteres.'})
 
    # 2. Valida la mayúscula
    if not re.search(r'[A-Z]', password):
        return jsonify({'status': 'error', 'msg': '⚠️ La contraseña falló: Debe contener al menos una letra mayúscula.'})
 
    # 3. Valida la minúscula
    if not re.search(r'[a-z]', password):
        return jsonify({'status': 'error', 'msg': '⚠️ La contraseña falló: Debe contener al menos una letra minúscula.'})
 
    # 4. Valida el carácter especial
    caracteres_especiales = r'[!"#$%&\'()*+,./:;<=>?@\[\\\]^_`{|}~-]'
    if not re.search(caracteres_especiales, password):
        return jsonify({'status': 'error', 'msg': '⚠️ La contraseña falló: Debe contener al menos un carácter especial.'})
 
    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        conexion.row_factory = sqlite3.Row
        cursor = conexion.cursor()
 
        # ── BÚSQUEDA 1: por correo real (no .temp) ────────────────────────────
        cursor.execute(
            """
            SELECT id_usuario, correo, contrasena, estado
            FROM tblusuario
            WHERE correo = ?
              AND correo IS NOT NULL
              AND correo != ''
              AND correo NOT LIKE '%@clinident.temp'
            """,
            [email]
        )
        por_correo = cursor.fetchone()
 
        # ── BÚSQUEDA 2: por teléfono (sin importar contraseña temporal) ───────
        usuario_fisico = None
        if not por_correo and telefono:
            cursor.execute(
                """
                SELECT id_usuario, correo, contrasena, estado
                FROM tblusuario
                WHERE telefono = ?
                """,
                [telefono]
            )
            fila = cursor.fetchone()
            if fila and _es_sin_cuenta(fila):
                usuario_fisico = fila
            elif fila and not _es_sin_cuenta(fila):
                # Teléfono pertenece a alguien con cuenta real → conflicto
                return jsonify({
                    'status': 'error',
                    'msg': '⚠️ El teléfono ya está asociado a otra cuenta activa.'
                })
 
        # ── BÚSQUEDA 3: nombre + apellido (fallback) ──────────────────────────
        if not por_correo and not usuario_fisico:
            cursor.execute(
                """
                SELECT id_usuario, correo, contrasena, estado
                FROM tblusuario
                WHERE LOWER(nombre)   = LOWER(?)
                  AND LOWER(apellido) = LOWER(?)
                """,
                [nombre, apellido]
            )
            fila = cursor.fetchone()
            if fila and _es_sin_cuenta(fila):
                usuario_fisico = fila
 
        # ── ESCENARIO A: correo real CON cuenta real → ya tiene cuenta ────────
        if por_correo and not _es_sin_cuenta(por_correo):
            return jsonify({
                'status': 'error',
                'msg': '⚠️ Este correo ya tiene una cuenta activa. Inicia sesión o usa "Recuperar cuenta".'
            })
 
        # ── Candidato a activar: puede venir de búsqueda 1, 2 o 3 ────────────
        candidato = por_correo if (por_correo and _es_sin_cuenta(por_correo)) else usuario_fisico
 
        # ── Validar teléfono duplicado para el caso 100% nuevo ────────────────
        if telefono and not candidato:
            cursor.execute(
                "SELECT id_usuario FROM tblusuario WHERE telefono = ?",
                [telefono]
            )
            fila = cursor.fetchone()
            if fila and not _es_sin_cuenta(fila):
                return jsonify({
                    'status': 'error',
                    'msg': '⚠️ El número de teléfono ya está registrado por otro usuario.'
                })
 
        # ── NADA se guarda en la BD todavía. Queda pendiente en sesión ────────
        # hasta que /verificar confirme el código de confirmación.
        session['registro_pendiente'] = {
            'id_usuario_candidato': candidato['id_usuario'] if candidato else None,
            'nombre':   nombre,
            'apellido': apellido,
            'email':    email,
            'telefono': telefono or None,
            'password': password
        }
 
        return jsonify({
            'status': 'success',
            'msg': 'Datos validados. Verifica con el código enviado a tu correo.'
        })
 
    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'msg': f'Error de base de datos: {str(e)}'})
 
    finally:
        if conexion:
            conexion.close()
 
 
@registro_blueprint.route('/verificar', methods=['POST'])
def verificar_codigo():
    """
    Verifica el código de confirmación. Solo si es correcto se escribe
    el usuario en la base de datos (INSERT o UPDATE, según corresponda).
    Código fijo de prueba (entorno SENA): SENA4
    """
    if request.is_json:
        datos  = request.get_json() or {}
        email  = datos.get('email',  '').strip()
        codigo = datos.get('codigo', '').strip().upper()
    else:
        email  = request.form.get('email',  '').strip()
        codigo = request.form.get('codigo', '').strip().upper()
 
    if not email or not codigo:
        return jsonify({'status': 'error', 'msg': 'Faltan datos para verificar la cuenta.'})
 
    pendiente = session.get('registro_pendiente')
    if not pendiente or pendiente['email'].lower() != email.lower():
        return jsonify({
            'status': 'error',
            'msg': '⚠️ No hay un registro pendiente para este correo. Vuelve a llenar el formulario.'
        })
 
    if codigo != CODIGO_VALIDO:
        return jsonify({'status': 'error', 'msg': '❌ Código incorrecto. Inténtalo de nuevo.'})
 
    conexion = None
    try:
        conexion = sqlite3.connect(RUTA_BD)
        cursor = conexion.cursor()
 
        if pendiente['id_usuario_candidato']:
            # Activar cuenta física existente (Escenario B)
            cursor.execute(
                """
                UPDATE tblusuario
                   SET correo     = ?,
                       nombre     = ?,
                       apellido   = ?,
                       telefono   = ?,
                       contrasena = ?,
                       estado     = 'Activo'
                 WHERE id_usuario = ?
                """,
                [pendiente['email'], pendiente['nombre'], pendiente['apellido'],
                 pendiente['telefono'], pendiente['password'], pendiente['id_usuario_candidato']]
            )
            mensaje = '¡Cuenta activada! Encontramos tu registro en la clínica.'
        else:
            # Usuario completamente nuevo (Escenario C)
            cursor.execute(
                """
                INSERT INTO tblusuario (id_rol, nombre, apellido, correo, telefono, contrasena, estado)
                VALUES (4, ?, ?, ?, ?, ?, 'Activo')
                """,
                [pendiente['nombre'], pendiente['apellido'], pendiente['email'],
                 pendiente['telefono'], pendiente['password']]
            )
            mensaje = '¡Cuenta creada con éxito en el sistema local!'
 
        conexion.commit()
        session.pop('registro_pendiente', None)
        return jsonify({'status': 'success', 'msg': mensaje})
 
    except sqlite3.IntegrityError as e:
        err = str(e).lower()
        if 'correo' in err or 'unique' in err:
            return jsonify({'status': 'error', 'msg': '⚠️ El correo electrónico ya se encuentra registrado.'})
        return jsonify({'status': 'error', 'msg': f'Error de integridad: {str(e)}'})
 
    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'msg': f'Error de base de datos: {str(e)}'})
 
    finally:
        if conexion:
            conexion.close()
 
 
@registro_blueprint.route('/limpiar_pendiente', methods=['POST'])
def limpiar_pendiente():
    """Limpia la marca de registro pendiente de la sesión (ej. si el usuario cancela)."""
    session.pop('registro_pendiente', None)
    return jsonify({'status': 'success'})
 