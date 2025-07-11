import os
import pandas as pd
from datetime import datetime
import sqlite3

def crearConexion(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Conexión exitosa a la base de datos: {db_file}")
    except sqlite3.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
    return conn

def cerrarConexion(conn):
    if conn:
        conn.close()
        print("Conexión cerrada.\n")

def crearTabla(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                piso INTEGER NOT NULL,
                oficina TEXT NOT NULL,
                quien TEXT NOT NULL,
                razon TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha TEXT DEFAULT (datetime('now'))
                )
                """)
    conn.commit()


def generarReporte(conn):
    try:
        piso = int(input("Ingrese el número de piso: "))
        oficina = input("Ingrese el nombre de la oficina: ")
        quien = input("Ingrese el nombre de quien reporta: ")
        razon = input("Ingrese la razón del reporte: ")
        estado = input("Ingrese el estado del reporte (pendiente, en proceso, resuelto): ")

        fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M")
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO datos (piso, oficina, quien, razon, estado, fecha)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (piso, oficina, quien, razon, estado, fecha_actual))

        conn.commit()
        print("Reporte generado exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al generar el reporte: {e}")
        

def mostrarReportes(conn):
    #mostrar ultimos 10 reportes
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datos ORDER BY id DESC LIMIT 10")
    reportes = cursor.fetchall()
    if reportes:
        print("Últimos 10 reportes:")
        for reporte in reportes:
            print(f"ID: {reporte[0]}, Piso: {reporte[1]}, Oficina: {reporte[2]}, Quien: {reporte[3]}, Razon: {reporte[4]}, Estado: {reporte[5]}, Fecha: {reporte[6]}")
    else:
        print("No hay reportes disponibles.")

def editarReporte(conn):
    try:
        id_reporte = int(input("Ingrese el ID del reporte a editar: "))
        nuevo_estado = input("Ingrese el nuevo estado del reporte (pendiente, en proceso, resuelto): ")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE datos
            SET estado = ?
            WHERE id = ?
        """, (nuevo_estado, id_reporte))

        conn.commit()
        if cursor.rowcount > 0:
            print("Reporte actualizado exitosamente.")
        else:
            print("No se encontró un reporte con ese ID.")
    except sqlite3.Error as e:
        print(f"Error al editar el reporte: {e}")

def eliminarReporte(conn):
    try:
        id_reporte = int(input("Ingrese el ID del reporte a eliminar: "))

        pregunta = input(f"¿Está seguro de que desea eliminar el reporte con ID {id_reporte}? (s/n): ")
        if pregunta.lower() == 's' or pregunta.lower() == 'si':
            cursor = conn.cursor()
            cursor.execute("DELETE FROM datos WHERE id = ?", (id_reporte,))
            conn.commit()
            if cursor.rowcount > 0:
                print("Reporte eliminado exitosamente.")
            else:
                print("No se encontró un reporte con ese ID.")
        else:
            print("Operación cancelada, no se eliminó ningún reporte.")
    except sqlite3.Error as e:
        print(f"Error al eliminar el reporte: {e}")
    
def buscarReporte(conn):
    pregunta = input("¿Desea buscar por ID o por estado? (id/estado): ").strip().lower()
    cursor = conn.cursor()
    if pregunta == 'id' or pregunta == "1":
        try:
            id_reporte = int(input("Ingrese el ID del reporte a buscar: "))
            cursor.execute("SELECT * FROM datos WHERE id = ?", (id_reporte,))
            reporte = cursor.fetchone()
            if reporte:
                print(f"Reporte encontrado: ID: {reporte[0]}, Piso: {reporte[1]}, Oficina: {reporte[2]}, Quien: {reporte[3]}, Razon: {reporte[4]}, Estado: {reporte[5]}, Fecha: {reporte[6]}")
            else:
                print("No se encontró un reporte con ese ID.")
        except ValueError:
            print("ID inválido, debe ser un número entero.")
    elif pregunta == 'estado' or pregunta == "2":
        estado = input("Ingrese el estado del reporte a buscar (pendiente, en proceso, resuelto): ")
        cursor.execute("SELECT * FROM datos WHERE estado = ?", (estado,))
        reportes = cursor.fetchall()
        if reportes:
            print(f"Reportes encontrados con estado '{estado}':")
            for reporte in reportes:
                print(f"ID: {reporte[0]}, Piso: {reporte[1]}, Oficina: {reporte[2]}, Quien: {reporte[3]}, Razon: {reporte[4]}, Estado: {reporte[5]}, Fecha: {reporte[6]}")
        else:
            print(f"No se encontraron reportes con estado '{estado}'.")

def exportarExcel():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(directorio_actual, "datosReportes.db")
    conn = crearConexion(db_file)
    
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datos")
        reportes = cursor.fetchall()
        
        if reportes:
            df = pd.DataFrame(reportes, columns=['ID', 'Piso', 'Oficina', 'Quien', 'Razon', 'Estado', 'Fecha'])
            archivo_excel = os.path.join(directorio_actual, "reportes.xlsx")
            df.to_excel(archivo_excel, index=False)
            print(f"Reportes exportados exitosamente a {archivo_excel}")
        else:
            print("No hay reportes para exportar.")
        
        cerrarConexion(conn)
    else:
        print("No se pudo conectar a la base de datos para exportar los reportes.")

def main():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(directorio_actual, "datosReportes.db")
    conn = crearConexion(db_file)
    print("Conectando a la base de datos...")
    if conn:
        crearTabla(conn)
        print ("Bienvenido al sistema de reportes")

        while True:
            print("\n====== Menú Principal ======\n")
            print("1. Generar reporte")
            print("2. Ver reportes existentes")
            print("3. editar estado de reporte")
            print("4. Eliminar reporte")
            print("5. Buscar reporte")
            print("6. Salir")
            print("7. Exportar a excel")
            print("\n============================\n")
            opcion = input("Seleccione una opción: ")
            print("\n")
            if opcion == '1':
                print("Generando reporte...\n")
                generarReporte(conn)
            elif opcion == '2':
                print("Mostrando reportes existentes...\n")
                mostrarReportes(conn)
            elif opcion == '3':
                print("Editando estado de reporte...\n")
                editarReporte(conn)
            elif opcion == '4':
                print("Eliminando reporte...\n")
                eliminarReporte(conn)
            elif opcion == '5':
                print("Buscando reporte...\n")
                buscarReporte(conn)
            elif opcion == '6':
                print("Saliendo del sistema...\n")
                break
            elif opcion == '7':
                exportarExcel(conn)
            else:
                print("Opción no válida, intente de nuevo.\n")
        pass
    cerrarConexion(conn)

main()