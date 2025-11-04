import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'datosReportes.db')
DB_OFICINAS_PATH = r'\\16.1.1.118\db\OficinasCne.db'

def inicializar_base_datos():
    """Crea o actualiza la estructura de la base de datos local"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla de reportes con todas las columnas necesarias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        piso INTEGER NOT NULL,
        oficina TEXT NOT NULL,
        quien TEXT NOT NULL,
        razon TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha TEXT DEFAULT (strftime('%d/%m/%y', 'now', 'localtime')),
        resuelto_por TEXT DEFAULT '',
        fecha_resolucion TEXT DEFAULT NULL
    )
    """)
    
    # Crear tabla de comentarios/notas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comentarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporte_id INTEGER NOT NULL,
        comentario TEXT NOT NULL,
        autor TEXT NOT NULL,
        fecha TEXT DEFAULT (strftime('%d/%m/%y %H:%M', 'now', 'localtime')),
        FOREIGN KEY (reporte_id) REFERENCES datos(id) ON DELETE CASCADE
    )
    """)
    
    # Verificar si necesitamos agregar columnas a datos existentes
    cursor.execute("PRAGMA table_info(datos)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    if 'resuelto_por' not in columnas:
        print("⚙️ Agregando columna 'resuelto_por' a tabla existente...")
        cursor.execute("ALTER TABLE datos ADD COLUMN resuelto_por TEXT DEFAULT ''")
    
    if 'fecha_resolucion' not in columnas:
        print("⚙️ Agregando columna 'fecha_resolucion' a tabla existente...")
        cursor.execute("ALTER TABLE datos ADD COLUMN fecha_resolucion TEXT DEFAULT NULL")
    
    conn.commit()
    conn.close()
    print("✅ Base de datos local inicializada correctamente")
    print(f"📁 Ubicación: {DB_PATH}")

def verificar_bd_oficinas():
    """Verifica la conexión a la base de datos remota de oficinas"""
    try:
        conn = sqlite3.connect(DB_OFICINAS_PATH)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla oficinas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='oficinas'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM oficinas")
            count = cursor.fetchone()[0]
            print(f"✅ Conexión exitosa a BD de oficinas remota")
            print(f"📍 {DB_OFICINAS_PATH}")
            print(f"📊 {count} oficinas encontradas")
            
            # Mostrar estructura de la tabla
            cursor.execute("PRAGMA table_info(oficinas)")
            columnas = cursor.fetchall()
            print(f"📋 Columnas disponibles: {', '.join([col[1] for col in columnas])}")
        else:
            print("⚠️ La tabla 'oficinas' no existe en la BD remota")
        
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error al conectar con BD de oficinas remota:")
        print(f"   {e}")
        print(f"   Verifica que la ruta {DB_OFICINAS_PATH} sea accesible")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def crear_tabla_oficinas_remota(cursor):
    """Crea la tabla oficinas en la BD remota si no existe"""
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS oficinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_oficina TEXT UNIQUE NOT NULL,
        piso INTEGER NOT NULL
    )
    """)

def cargar_oficinas_ejemplo():
    """Carga oficinas de ejemplo en la BD remota"""
    try:
        conn = sqlite3.connect(DB_OFICINAS_PATH)
        cursor = conn.cursor()
        
        oficinas_ejemplo = [
            ('Recepción', 0),
            ('Administración', 1),
            ('Contabilidad', 1),
            ('RRHH', 2),
            ('IT', 2),
            ('Sistemas', 2),
            ('Gerencia', 3),
            ('Dirección', 4),
            ('Archivo', -1),
            ('Depósito', -2),
            ('Estacionamiento', -3),
        ]
        
        for nombre, piso in oficinas_ejemplo:
            try:
                cursor.execute("INSERT INTO oficinas (nombre_oficina, piso) VALUES (?, ?)", (nombre, piso))
                print(f"  ✓ Oficina '{nombre}' (Piso {piso}) agregada")
            except sqlite3.IntegrityError:
                print(f"  - Oficina '{nombre}' ya existe")
        
        conn.commit()
        conn.close()
        print("✅ Oficinas cargadas exitosamente")
    except Exception as e:
        print(f"❌ Error al cargar oficinas: {e}")

if __name__ == "__main__":
    print("🚀 Inicializando sistema de reportes...\n")
    print("=" * 50)
    
    # Inicializar BD local
    inicializar_base_datos()
    print()
    
    # Verificar BD remota de oficinas
    print("=" * 50)
    print("Verificando base de datos de oficinas...")
    if verificar_bd_oficinas():
        print()
        respuesta = input("¿Deseas cargar oficinas de ejemplo en la BD remota? (s/n): ").lower()
        if respuesta == 's':
            cargar_oficinas_ejemplo()
    
    print("\n" + "=" * 50)
    print("✨ ¡Inicialización completa!")
    print("📝 Ejecuta 'python app.py' para iniciar el servidor")