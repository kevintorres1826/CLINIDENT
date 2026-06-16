from flask import Blueprint, jsonify, session
import sqlite3
import os
import sys
 
facturacion_blueprint = Blueprint('facturacion', __name__)
 
# ─── Ruta a la BD ───────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    ruta_exe = os.path.dirname(sys.executable)
else:
    ruta_exe = os.path.dirname(os.path.abspath(__file__))
    ruta_exe = os.path.dirname(ruta_exe)
 
RUTA_BD = os.path.join(ruta_exe, "clinident.db")
 
 
def get_db():
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row
    return conn
 
 
def _migrar():
    """Migraciones seguras: añade columnas nuevas si no existen."""
    migraciones = [
        "ALTER TABLE tbltratamiento ADD COLUMN id_cita INTEGER REFERENCES tblcita(id_cita)",
        "ALTER TABLE tblcita ADD COLUMN tratamiento VARCHAR(100) DEFAULT NULL",
        "ALTER TABLE tbltratamiento ADD COLUMN cobro_extra DECIMAL(12,2) DEFAULT 0.00",
    ]
    conn = sqlite3.connect(RUTA_BD)
    for sql in migraciones:
        try:
            conn.execute(sql)
        except Exception:
            pass  # Columna ya existe → ignorar
    conn.commit()
    conn.close()
 
 
_migrar()
 
 
# ─── GET /facturacion/citas-pendientes ──────────────────────────────────────
@facturacion_blueprint.route('/citas-pendientes', methods=['GET'])
def citas_pendientes():
    try:
        conn = get_db()
        cursor = conn.cursor()
 
        cursor.execute("""
            SELECT
                c.id_cita,
                c.fecha,
                c.hora_inicio,
                c.hora_fin,
                c.tratamiento,                               -- ← nombre guardado al agendar
                pac.nombre  || ' ' || pac.apellido  AS nombre_paciente,
                pac.id_usuario                       AS id_paciente,
                odo.nombre  || ' ' || odo.apellido  AS nombre_odontologo,
                odo.id_usuario                       AS id_odontologo,
                s.nombre_sala,
                e.nombre_estado
            FROM tblcita c
            JOIN tblusuario    pac ON pac.id_usuario = c.id_usuario
            JOIN tblusuario    odo ON odo.id_usuario = c.id_odontologo
            JOIN tblsala       s   ON s.id_sala      = c.id_sala
            JOIN tblagenda     a   ON a.id_cita      = c.id_cita
            JOIN tblestadocita e   ON e.id_estado    = a.id_estado
            WHERE a.id_estado IN (1, 4)
              AND c.id_cita NOT IN (
                    SELECT t.id_cita
                    FROM tbltratamiento t
                    JOIN tblfactura f ON f.id_tratamiento = t.id_tratamiento
                    WHERE t.id_cita IS NOT NULL
              )
            ORDER BY c.fecha ASC, c.hora_inicio ASC
        """)
 
        filas = cursor.fetchall()
        conn.close()
        return jsonify({"status": "success", "citas": [dict(f) for f in filas]})
 
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
 
 
# ─── GET /facturacion/tratamientos-odontologo/<id> ──────────────────────────
@facturacion_blueprint.route('/tratamientos-odontologo/<int:id_odo>', methods=['GET'])
def tratamientos_por_odontologo(id_odo):
    try:
        conn = get_db()
        cursor = conn.cursor()
 
        cursor.execute("""
            SELECT
                id_tipo,
                nombre,
                COALESCE(precio_base, 0) AS precio_base
            FROM tbltipotratamiento
            WHERE nombre IN (
                'Limpieza dental',
                'Revisión general',
                'Ortodoncia',
                'Endodoncia',
                'Cirugía oral'
            )
            ORDER BY nombre ASC
        """)
        filas = cursor.fetchall()
        conn.close()
        return jsonify({"status": "success", "tratamientos": [dict(f) for f in filas]})

 
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
 
 
# ─── POST /facturacion/registrar ────────────────────────────────────────────
@facturacion_blueprint.route('/registrar', methods=['POST'])
def registrar_factura():
    from flask import request
    data = request.get_json()
 
    required = ["id_cita", "id_odontologo", "id_paciente",
                "id_tipo", "diagnostico", "cobro_extra", "id_metodo_pago"]
    for campo in required:
        if campo not in data:
            return jsonify({"status": "error",
                            "message": f"Campo requerido faltante: {campo}"}), 400

    try:
        descuento   = float(data.get("descuento", 0))
        impuesto    = float(data.get("impuesto",  0))
        cobro_extra = float(data["cobro_extra"])

        conn = get_db()
        cursor = conn.cursor()

        # Precio base definido en el tipo de tratamiento
        cursor.execute("SELECT COALESCE(precio_base, 0) FROM tbltipotratamiento WHERE id_tipo = ?", (data["id_tipo"],))
        row = cursor.fetchone()
        precio_base = float(row[0]) if row else 0.0

        subtotal    = precio_base + cobro_extra
        valor_final = subtotal * (1 - descuento / 100) * (1 + impuesto / 100)

        cursor.execute("""
            INSERT INTO tbltratamiento (id_tipo, diagnostico, valor, cobro_extra, id_odontologo, id_usuario, id_cita)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data["id_tipo"], data["diagnostico"], round(valor_final, 2), round(cobro_extra, 2),
              data["id_odontologo"], data["id_paciente"], data["id_cita"]))
        id_tratamiento = cursor.lastrowid
 
        cursor.execute("INSERT INTO tblfactura (id_tratamiento) VALUES (?)", (id_tratamiento,))
        id_factura = cursor.lastrowid
 
        cursor.execute("""
            INSERT INTO tblhistorialfacturacion (id_factura, fecha_emision)
            VALUES (?, date('now'))
        """, (id_factura,))
 
        cursor.execute("""
            INSERT INTO tblpago (id_factura, id_metodo, pagado, fecha_pago)
            VALUES (?, ?, 1, date('now'))
        """, (id_factura, data["id_metodo_pago"]))
 
        cursor.execute("UPDATE tblagenda SET id_estado = 4 WHERE id_cita = ?", (data["id_cita"],))
 
        conn.commit()
        conn.close()
 
        return jsonify({
            "status":         "success",
            "message":        "Factura registrada correctamente",
            "id_factura":     id_factura,
            "id_tratamiento": id_tratamiento,
            "valor_final":    round(valor_final, 2)
        })
 
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
 