import os
import sqlite3
from flask import jsonify

# Autodetecta la ubicación del .db al lado de este archivo (Ideal para portables)
# __file__ en Python es el equivalente exacto a __DIR__ en PHP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(BASE_DIR, 'clinident.db')

def obtener_conexion():
    """
    Establece y configura la conexión nativa a la base de datos SQLite.
    Equivalente exacto a la configuración PDO de tu conexion.php
    """
    try:
        # Conexión nativa a SQLite
        conexion = sqlite3.connect(RUTA_DB)
        
        # Forzar que SQLite reporte cualquier error inmediatamente (Habilitado por defecto en sqlite3)
        # Retornar los datos limpios en diccionarios asociativos (Equivalente a PDO::FETCH_ASSOC)
        conexion.row_factory = sqlite3.Row
        
        # Activar soporte interno de llaves foráneas para mantener la integridad de las tablas
        conexion.execute("PRAGMA foreign_keys = ON;")
        
        return conexion

    except sqlite3.Error as e:
        # Manejo del error en el mismo formato estructurado de tu PHP
        # Nota: En Flask, para retornar JSON en un fallo de conexión global, 
        # lanzamos una respuesta estructurada que tus rutas capturarán.
        response = jsonify({
            'status': 'error',
            'msg': 'Error de portabilidad: No se encontró o no se pudo abrir clinident.db. Asegúrate de que esté junto al ejecutable.'
        })
        response.status_code = 500
        return response