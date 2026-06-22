
"""
Script de diagnóstico — ejecútalo en la MISMA carpeta donde está clinident.db
(la raíz de tu proyecto, junto a main.py / app.py).
 
Uso:
    python diagnostico_bd.py
"""
import sqlite3
import os
 
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinident.db")
 
if not os.path.exists(RUTA_BD):
    print(f"❌ No se encontró clinident.db en: {RUTA_BD}")
    print("   Copia este script a la carpeta raíz de tu proyecto (junto a main.py) y vuelve a ejecutarlo.")
    exit(1)
 
conn = sqlite3.connect(RUTA_BD)
cur = conn.cursor()
 
print(f"📁 Base de datos: {RUTA_BD}\n")
 
# 1. Ver columnas reales de tblpago
print("── Columnas actuales de tblpago ──")
cur.execute("PRAGMA table_info(tblpago)")
columnas = cur.fetchall()
nombres_columnas = [c[1] for c in columnas]
for c in columnas:
    print(f"  {c[1]:20s} {c[2]}")
 
tiene_monto = "monto_recibido" in nombres_columnas
tiene_cambio = "cambio" in nombres_columnas
 
print(f"\n¿Tiene 'monto_recibido'? {'✅ SÍ' if tiene_monto else '❌ NO — la migración no se aplicó'}")
print(f"¿Tiene 'cambio'?         {'✅ SÍ' if tiene_cambio else '❌ NO — la migración no se aplicó'}")
 
# 2. Ver columnas reales de tbltratamiento (para 'impuesto')
print("\n── Columnas actuales de tbltratamiento ──")
cur.execute("PRAGMA table_info(tbltratamiento)")
columnas2 = cur.fetchall()
nombres2 = [c[1] for c in columnas2]
for c in columnas2:
    print(f"  {c[1]:20s} {c[2]}")
print(f"\n¿Tiene 'impuesto'? {'✅ SÍ' if 'impuesto' in nombres2 else '❌ NO — la migración no se aplicó'}")
 
# 3. Mostrar las últimas 5 filas de tblpago tal cual están guardadas
if tiene_monto and tiene_cambio:
    print("\n── Últimos 5 registros de tblpago ──")
    cur.execute("SELECT * FROM tblpago ORDER BY id_pago DESC LIMIT 5")
    filas = cur.fetchall()
    col_names = [d[0] for d in cur.description]
    print("  " + " | ".join(col_names))
    for f in filas:
        print("  " + " | ".join(str(x) for x in f))
 
conn.close()
 