import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'datosReportes.db')

print("🗑️ Eliminando columna 'fecha_resolucion'...\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# SQLite no permite DROP COLUMN directamente, hay que recrear la tabla
try:
    # 1. Crear tabla temporal sin fecha_resolucion
    cursor.execute("""
    CREATE TABLE datos_temp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        piso INTEGER NOT NULL,
        oficina TEXT NOT NULL,
        quien TEXT NOT NULL,
        razon TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha TEXT DEFAULT (strftime('%d/%m/%y', 'now', 'localtime')),
        resuelto_por TEXT DEFAULT ''
    )
    """)
    
    # 2. Copiar datos (sin fecha_resolucion)
    cursor.execute("""
    INSERT INTO datos_temp (id, piso, oficina, quien, razon, estado, fecha, resuelto_por)
    SELECT id, piso, oficina, quien, razon, estado, fecha, resuelto_por
    FROM datos
    """)
    
    # 3. Eliminar tabla original
    cursor.execute("DROP TABLE datos")
    
    # 4. Renombrar tabla temporal
    cursor.execute("ALTER TABLE datos_temp RENAME TO datos")
    
    conn.commit()
    print("✅ Columna 'fecha_resolucion' eliminada exitosamente")
    print("✅ Todos los datos se mantuvieron intactos\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

conn.close()