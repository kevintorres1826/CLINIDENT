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
    Orden de búsqueda para detectar un alta física previa:
      1. Por correo exacto (no .temp)
      2. Por teléfono exacto          ← más confiable
      3. Por nombre + apellido        ← fallback
 
    Escenarios:
      A) Correo real encontrado CON cuenta real  → error, ya tiene cuenta.
      B) Coincidencia SIN cuenta real            → UPDATE, activa la cuenta.
      C) Nada coincide                           → INSERT nuevo paciente.
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
            # Excepción: si este correo fue registrado en ESTA sesión y aún no verificó,
            # el usuario retrocedió desde el paso 2 para reenviar el código.
            pendiente = session.get('registro_pendiente_correo', '')
            if pendiente and pendiente.lower() == email.lower():
                # Actualizar datos por si los cambió al retroceder
                cursor.execute(
                    "UPDATE tblusuario SET contrasena = ?, nombre = ?, apellido = ?, telefono = ? WHERE correo = ?",
                    [password, nombre, apellido, telefono or None, email]
                )
                conexion.commit()
                return jsonify({
                    'status': 'success',
                    'msg': 'Código reenviado. Verifica tu correo.'
                })
            return jsonify({
                'status': 'error',
                'msg': '⚠️ Este correo ya tiene una cuenta activa. Inicia sesión o usa "Recuperar cuenta".'
            })
 
        # ── Candidato a activar: puede venir de búsqueda 1, 2 o 3 ────────────
        candidato = por_correo if (por_correo and _es_sin_cuenta(por_correo)) else usuario_fisico
 
        # ── ESCENARIO B: activar cuenta física existente ──────────────────────
        if candidato:
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
                [email, nombre, apellido, telefono or None, password, candidato['id_usuario']]
            )
            conexion.commit()
            session['registro_pendiente_correo'] = email
            return jsonify({
                'status': 'success',
                'msg': '¡Cuenta activada! Encontramos tu registro en la clínica. Verifica con el código.'
            })
 
        # ── ESCENARIO C: todo nuevo → INSERT ──────────────────────────────────
        # Validar que el teléfono no esté en uso por un usuario con cuenta real
        if telefono:
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
 
        cursor.execute(
            """
            INSERT INTO tblusuario (id_rol, nombre, apellido, correo, telefono, contrasena, estado)
            VALUES (4, ?, ?, ?, ?, ?, 'Activo')
            """,
            [nombre, apellido, email, telefono or None, password]
        )
        conexion.commit()
        session['registro_pendiente_correo'] = email
        return jsonify({
            'status': 'success',
            'msg': 'Cuenta creada con éxito en el sistema local.'
        })
 
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
    """Limpia la marca de registro pendiente de la sesión al finalizar con éxito."""
    session.pop('registro_pendiente_correo', None)
    return jsonify({'status': 'success'})