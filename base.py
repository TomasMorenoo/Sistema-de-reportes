import sqlite3

conn = sqlite3.connect('datosReportes.db')
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS datos;")

cur.execute("""
CREATE TABLE datos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    piso INTEGER NOT NULL,
    oficina TEXT NOT NULL,
    quien TEXT NOT NULL,
    razon TEXT NOT NULL,
    estado TEXT NOT NULL,
    fecha TEXT DEFAULT (strftime('%d/%m/%y %H:%M', 'now', 'localtime'))
);
""")

conn.commit()
conn.close()
print("Tabla datos recreada correctamente.")
