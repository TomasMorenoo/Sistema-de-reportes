"""
Manejo de conexiones a base de datos
"""
import sqlite3
from config import DB_PATH, DB_OFICINAS_PATH

def obtener_conexion():
    """Conexión a la BD local de reportes"""
    return sqlite3.connect(DB_PATH)

def obtener_conexion_oficinas():
    """Conexión a la BD remota de oficinas"""
    try:
        return sqlite3.connect(DB_OFICINAS_PATH)
    except sqlite3.Error as e:
        print(f"Error al conectar con BD de oficinas: {e}")
        return None

def obtener_pisos_disponibles():
    """Obtiene lista de pisos únicos"""
    try:
        conn_oficinas = obtener_conexion_oficinas()
        if conn_oficinas:
            cur = conn_oficinas.cursor()
            cur.execute("SELECT DISTINCT piso FROM oficinas ORDER BY piso")
            pisos = [str(p[0]) for p in cur.fetchall()]
            conn_oficinas.close()
            return pisos
    except:
        pass
    return ['1', '2', '3', '4', '5']

def obtener_oficinas_por_piso(piso):
    """Obtiene oficinas de un piso específico"""
    try:
        conn_oficinas = obtener_conexion_oficinas()
        if conn_oficinas:
            cur = conn_oficinas.cursor()
            cur.execute("SELECT nombre_oficina FROM oficinas WHERE piso = ? ORDER BY nombre_oficina", (piso,))
            oficinas = [o[0] for o in cur.fetchall()]
            conn_oficinas.close()
            return oficinas
    except:
        pass
    return []
