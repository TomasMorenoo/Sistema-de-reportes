import sqlite3

DB_OFICINAS_PATH = r'\\16.1.1.118\db\OficinasCne.db'

def conectar():
    """Conecta a la base de datos remota de oficinas"""
    try:
        conn = sqlite3.connect(DB_OFICINAS_PATH)
        print(f"✅ Conectado a: {DB_OFICINAS_PATH}\n")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error de conexión: {e}")
        print(f"   Verifica que la ruta {DB_OFICINAS_PATH} sea accesible")
        return None

def crear_tabla_si_no_existe(conn):
    """Crea la tabla oficinas si no existe"""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS oficinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_oficina TEXT UNIQUE NOT NULL,
        piso INTEGER NOT NULL
    )
    ''')
    conn.commit()
    print("📋 Tabla 'oficinas' verificada/creada\n")

def listar_oficinas(conn):
    """Muestra todas las oficinas organizadas por piso"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM oficinas")
    total = cursor.fetchone()[0]
    
    if total == 0:
        print("ℹ️ No hay oficinas cargadas en la base de datos\n")
        return
    
    print(f"📊 Total de oficinas: {total}\n")
    print("=" * 50)
    
    cursor.execute("SELECT nombre_oficina, piso FROM oficinas ORDER BY piso, nombre_oficina")
    oficinas = cursor.fetchall()
    
    piso_actual = None
    for nombre, piso in oficinas:
        if piso != piso_actual:
            print(f"\n🏢 PISO {piso}")
            print("-" * 50)
            piso_actual = piso
        print(f"  • {nombre}")
    print("\n" + "=" * 50 + "\n")

def agregar_oficina(conn, nombre, piso):
    """Agrega una nueva oficina"""
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO oficinas (nombre_oficina, piso) VALUES (?, ?)", (nombre, piso))
        conn.commit()
        print(f"✅ Oficina '{nombre}' en piso {piso} agregada exitosamente\n")
        return True
    except sqlite3.IntegrityError:
        print(f"⚠️ La oficina '{nombre}' ya existe en la base de datos\n")
        return False
    except Exception as e:
        print(f"❌ Error al agregar oficina: {e}\n")
        return False

def eliminar_oficina(conn, nombre):
    """Elimina una oficina por nombre"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM oficinas WHERE nombre_oficina = ?", (nombre,))
    conn.commit()
    
    if cursor.rowcount > 0:
        print(f"🗑️ Oficina '{nombre}' eliminada exitosamente\n")
        return True
    else:
        print(f"⚠️ No se encontró la oficina '{nombre}'\n")
        return False

def menu_principal():
    """Menú interactivo para gestionar oficinas"""
    conn = conectar()
    if not conn:
        return
    
    crear_tabla_si_no_existe(conn)
    
    while True:
        print("\n" + "=" * 50)
        print("  GESTIÓN DE OFICINAS - Base de Datos Remota")
        print("=" * 50)
        print("\n1. 📋 Listar todas las oficinas")
        print("2. ➕ Agregar nueva oficina")
        print("3. ➕ Agregar múltiples oficinas")
        print("4. 🗑️ Eliminar oficina")
        print("5. 🚪 Salir")
        print("\n" + "=" * 50)
        
        opcion = input("\nSelecciona una opción: ").strip()
        
        if opcion == '1':
            print("\n")
            listar_oficinas(conn)
            
        elif opcion == '2':
            print("\n--- Agregar Nueva Oficina ---")
            nombre = input("Nombre de la oficina: ").strip()
            if not nombre:
                print("⚠️ El nombre no puede estar vacío\n")
                continue
            
            while True:
                piso_input = input("Piso (entre -3 y 4): ").strip()
                try:
                    piso = int(piso_input)
                    if -3 <= piso <= 4:
                        break
                    else:
                        print("⚠️ El piso debe estar entre -3 y 4")
                except ValueError:
                    print("❌ Ingresa un número válido")
            
            agregar_oficina(conn, nombre, piso)
            
        elif opcion == '3':
            print("\n--- Agregar Múltiples Oficinas ---")
            print("Ingresa las oficinas una por una.")
            print("Para terminar, deja el nombre vacío y presiona Enter.\n")
            
            contador = 0
            while True:
                nombre = input(f"\nOficina #{contador + 1} - Nombre: ").strip()
                if nombre == "":
                    break
                
                while True:
                    piso_input = input(f"Oficina #{contador + 1} - Piso (entre -3 y 4): ").strip()
                    try:
                        piso = int(piso_input)
                        if -3 <= piso <= 4:
                            break
                        else:
                            print("⚠️ El piso debe estar entre -3 y 4")
                    except ValueError:
                        print("❌ Ingresa un número válido")
                
                if agregar_oficina(conn, nombre, piso):
                    contador += 1
            
            print(f"\n✨ Proceso finalizado. Se agregaron {contador} oficinas nuevas.\n")
            
        elif opcion == '4':
            print("\n--- Eliminar Oficina ---")
            nombre = input("Nombre de la oficina a eliminar: ").strip()
            if nombre:
                confirmar = input(f"¿Estás seguro de eliminar '{nombre}'? (s/n): ").strip().lower()
                if confirmar == 's':
                    eliminar_oficina(conn, nombre)
            else:
                print("⚠️ El nombre no puede estar vacío\n")
                
        elif opcion == '5':
            print("\n👋 Cerrando conexión...")
            conn.close()
            print("✅ ¡Hasta luego!\n")
            break
            
        else:
            print("\n❌ Opción inválida. Intenta de nuevo.\n")

if __name__ == "__main__":
    print("\n🚀 Iniciando gestor de oficinas...\n")
    menu_principal()