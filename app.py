from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import openpyxl
from io import BytesIO
import os
import datetime  # Para generar la fecha desde Python

app = Flask(__name__)

def obtener_conexion():
    return sqlite3.connect('datosReportes.db')

def obtener_oficinas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM oficinas ORDER BY nombre ASC")
    oficinas = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return oficinas

@app.route('/debugdb')
def debugdb():
    return os.path.abspath('datosReportes.db')

@app.route('/')
def index():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datos ORDER BY id DESC")
    reportes = cursor.fetchall()
    conn.close()
    return render_template('index.html', reportes=reportes)

@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo_reporte():
    if request.method == 'POST':
        piso    = request.form['piso']
        oficina = request.form['oficina']
        quien   = request.form['quien']
        razon   = request.form['razon']
        estado  = request.form['estado']

        # Crear la fecha desde Python
        fecha = datetime.datetime.now().strftime("%d/%m/%y %H:%M")

        # Insertar en la base de datos con fecha incluida
        conn = obtener_conexion()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO datos (piso, oficina, quien, razon, estado, fecha)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (piso, oficina, quien, razon, estado, fecha))
        conn.commit()
        conn.close()
        return redirect('/')

    oficinas = obtener_oficinas()
    return render_template('nuevo.html', oficinas=oficinas)

@app.route('/excel')
def generar_excel():
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("SELECT * FROM datos ORDER BY id DESC")
    filas = cur.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reportes"
    ws.append(['ID', 'Piso', 'Oficina', 'Quién', 'Razón', 'Estado', 'Fecha'])

    for f in filas:
        ws.append(f)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='reportes.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/estadisticas')
def estadisticas():
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM datos")
    total = cur.fetchone()[0]

    cur.execute("SELECT estado, COUNT(*) FROM datos GROUP BY estado")
    por_estado = cur.fetchall()

    cur.execute("""
        SELECT LOWER(oficina) AS oficina_normalizada, COUNT(*) 
        FROM datos 
        GROUP BY oficina_normalizada 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    por_oficina = cur.fetchall()

    cur.execute("SELECT piso, COUNT(*) FROM datos GROUP BY piso ORDER BY piso ASC")
    por_piso = cur.fetchall()

    conn.close()

    return render_template(
        'estadisticas.html',
        total=total,
        por_estado=por_estado,
        por_oficina=por_oficina,
        por_piso=por_piso
    )

@app.route('/actualizar', methods=['GET', 'POST'])
def actualizar_estado():
    conn = obtener_conexion()
    cursor = conn.cursor()

    if request.method == 'POST':
        id_reporte = request.form['id_reporte']
        cursor.execute("UPDATE datos SET estado = 'resuelto' WHERE id = ?", (id_reporte,))
        conn.commit()

    # Mostrar tanto "pendiente" como "en proceso"
    cursor.execute("""
        SELECT id, piso, oficina, quien, razon, estado, fecha 
        FROM datos 
        WHERE estado IN ('pendiente', 'en proceso')
        ORDER BY id DESC
    """)
    reportes = cursor.fetchall()
    conn.close()
    return render_template('actualizar.html', reportes=reportes)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

