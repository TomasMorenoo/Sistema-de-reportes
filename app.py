from flask import Flask, render_template, request, redirect, send_file, flash, jsonify
import sqlite3
import openpyxl
from io import BytesIO
import os
from datetime import datetime
import json
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-cambiar-en-produccion'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'datosReportes.db')
DB_OFICINAS_PATH = r'\\16.1.1.118\db\OficinasCne.db'

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

@app.route('/')
def index():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        
        # Obtener filtros de la URL
        filtro_estado = request.args.get('estado', '')
        filtro_piso = request.args.get('piso', '')
        busqueda = request.args.get('busqueda', '')
        limite = request.args.get('limite', '50')
        pagina_actual = int(request.args.get('pagina', 1))
        
        # Construir query con filtros
        query = """
            SELECT d.*, 
                   (SELECT COUNT(*) FROM comentarios WHERE reporte_id = d.id) as num_comentarios
            FROM datos d 
            WHERE 1=1
        """
        params = []
        
        if filtro_estado:
            query += " AND d.estado = ?"
            params.append(filtro_estado)
        
        if filtro_piso:
            query += " AND d.piso = ?"
            params.append(filtro_piso)
        
        if busqueda:
            query += " AND (d.oficina LIKE ? OR d.quien LIKE ? OR d.razon LIKE ?)"
            busqueda_param = f"%{busqueda}%"
            params.extend([busqueda_param, busqueda_param, busqueda_param])
        
        query += " ORDER BY d.id DESC"
        
        # Obtener total de reportes
        query_total = """
            SELECT COUNT(*)
            FROM datos d
            WHERE 1=1
        """
        params_total = []
        
        if filtro_estado:
            query_total += " AND d.estado = ?"
            params_total.append(filtro_estado)
        
        if filtro_piso:
            query_total += " AND d.piso = ?"
            params_total.append(filtro_piso)
        
        if busqueda:
            query_total += " AND (d.oficina LIKE ? OR d.quien LIKE ? OR d.razon LIKE ?)"
            params_total.extend([busqueda_param, busqueda_param, busqueda_param])
        
        cur.execute(query_total, params_total)
        total_reportes = cur.fetchone()[0]
        
        # Calcular paginación
        total_paginas = 1
        offset = 0
        
        if limite != 'todos':
            try:
                limite_num = int(limite)
                total_paginas = (total_reportes + limite_num - 1) // limite_num
                offset = (pagina_actual - 1) * limite_num
                query += f" LIMIT {limite_num} OFFSET {offset}"
            except ValueError:
                limite = '50'
                limite_num = 50
                total_paginas = (total_reportes + 50 - 1) // 50
                query += " LIMIT 50"
        
        cur.execute(query, params)
        reportes = cur.fetchall()
        
        # Obtener pisos únicos para el filtro
        cur.execute("SELECT DISTINCT piso FROM datos ORDER BY piso")
        pisos_disponibles = [p[0] for p in cur.fetchall()]
        
        conn.close()
        
        try:
            limite_int = int(limite) if limite != 'todos' else limite
        except:
            limite_int = 50
        
        return render_template('index.html', 
                             reportes=reportes,
                             total_reportes=total_reportes,
                             pisos_disponibles=pisos_disponibles,
                             filtro_estado=filtro_estado,
                             filtro_piso=filtro_piso,
                             busqueda=busqueda,
                             limite=limite_int,
                             pagina_actual=pagina_actual,
                             total_paginas=total_paginas)
    except Exception as e:
        return f"Error al cargar reportes: {str(e)}", 500

@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo_reporte():
    if request.method == 'POST':
        try:
            piso = request.form['piso']
            oficina = request.form['oficina']
            quien = request.form['quien'].strip()
            razon = request.form['razon'].strip()
            estado = request.form['estado']
            resuelto_por = request.form.get('resuelto_por', '').strip() if estado == 'resuelto' else ''
            fecha = datetime.now().strftime("%d/%m/%y")

            if not quien or not razon:
                flash('Todos los campos son obligatorios', 'error')
                return redirect('/nuevo')

            conn = obtener_conexion()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO datos (piso, oficina, quien, razon, estado, fecha, resuelto_por)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (piso, oficina, quien, razon, estado, fecha, resuelto_por))
            conn.commit()
            conn.close()
            
            flash('Reporte creado exitosamente', 'success')
            return redirect('/')
        except Exception as e:
            flash(f'Error al crear reporte: {str(e)}', 'error')
            return redirect('/nuevo')

    oficinas_por_piso = defaultdict(list)
    
    conn_oficinas = obtener_conexion_oficinas()
    if conn_oficinas:
        try:
            cur = conn_oficinas.cursor()
            cur.execute("SELECT nombre_oficina, piso FROM oficinas ORDER BY piso, nombre_oficina")
            oficinas = cur.fetchall()
            conn_oficinas.close()
            
            for nombre, piso in oficinas:
                oficinas_por_piso[str(piso)].append(nombre)
        except Exception as e:
            print(f"Error al cargar oficinas: {e}")
            flash('No se pudieron cargar las oficinas desde el servidor', 'warning')
    else:
        flash('No se pudo conectar a la base de datos de oficinas', 'error')

    oficinas_json = json.dumps(oficinas_por_piso)
    return render_template('nuevo.html', oficinas_json=oficinas_json)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_reporte(id):
    conn = obtener_conexion()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            piso = request.form['piso']
            oficina = request.form['oficina']
            quien = request.form['quien'].strip()
            razon = request.form['razon'].strip()
            estado = request.form['estado']
            
            if estado == 'resuelto':
                resuelto_por = request.form.get('resuelto_por', '').strip()
                cur.execute("""
                    UPDATE datos 
                    SET piso=?, oficina=?, quien=?, razon=?, estado=?, resuelto_por=?
                    WHERE id=?
                """, (piso, oficina, quien, razon, estado, resuelto_por, id))
            else:
                cur.execute("""
                    UPDATE datos 
                    SET piso=?, oficina=?, quien=?, razon=?, estado=?, resuelto_por=''
                    WHERE id=?
                """, (piso, oficina, quien, razon, estado, id))
            
            conn.commit()
            conn.close()
            flash(f'Reporte #{id} actualizado exitosamente', 'success')
            return redirect('/')
            
        except Exception as e:
            conn.close()
            flash(f'Error al actualizar reporte: {str(e)}', 'error')
            return redirect(f'/editar/{id}')
    
    cur.execute("SELECT * FROM datos WHERE id = ?", (id,))
    reporte = cur.fetchone()
    
    if not reporte:
        conn.close()
        flash(f'Reporte #{id} no encontrado', 'error')
        return redirect('/')
    
    oficinas_por_piso = defaultdict(list)
    conn_oficinas = obtener_conexion_oficinas()
    if conn_oficinas:
        try:
            cur_oficinas = conn_oficinas.cursor()
            cur_oficinas.execute("SELECT nombre_oficina, piso FROM oficinas ORDER BY piso, nombre_oficina")
            oficinas = cur_oficinas.fetchall()
            conn_oficinas.close()
            
            for nombre, piso in oficinas:
                oficinas_por_piso[str(piso)].append(nombre)
        except Exception as e:
            print(f"Error al cargar oficinas: {e}")
    
    oficinas_json = json.dumps(oficinas_por_piso)
    
    cur.execute("SELECT * FROM comentarios WHERE reporte_id = ? ORDER BY id DESC", (id,))
    comentarios = cur.fetchall()
    
    conn.close()
    return render_template('editar.html', reporte=reporte, oficinas_json=oficinas_json, comentarios=comentarios)

@app.route('/comentario/<int:reporte_id>', methods=['POST'])
def agregar_comentario(reporte_id):
    try:
        comentario = request.form.get('comentario', '').strip()
        autor = request.form.get('autor', '').strip()
        
        if not comentario or not autor:
            flash('El comentario y el autor son obligatorios', 'error')
            return redirect(f'/editar/{reporte_id}')
        
        fecha_actual = datetime.now().strftime("%d/%m/%y %H:%M")
        
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO comentarios (reporte_id, comentario, autor, fecha)
            VALUES (?, ?, ?, ?)
        """, (reporte_id, comentario, autor, fecha_actual))
        conn.commit()
        conn.close()
        
        flash('Comentario agregado exitosamente', 'success')
        return redirect(f'/editar/{reporte_id}')
    except Exception as e:
        flash(f'Error al agregar comentario: {str(e)}', 'error')
        return redirect(f'/editar/{reporte_id}')

@app.route('/eliminar_comentario/<int:comentario_id>/<int:reporte_id>', methods=['POST'])
def eliminar_comentario(comentario_id, reporte_id):
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("DELETE FROM comentarios WHERE id = ?", (comentario_id,))
        conn.commit()
        conn.close()
        flash('Comentario eliminado exitosamente', 'success')
        return redirect(f'/editar/{reporte_id}')
    except Exception as e:
        flash(f'Error al eliminar comentario: {str(e)}', 'error')
        return redirect(f'/editar/{reporte_id}')

@app.route('/resolver_rapido', methods=['POST'])
def resolver_rapido():
    try:
        id_reporte = request.form.get('id_reporte')
        resuelto_por = request.form.get('resuelto_por', '').strip()
        
        if not resuelto_por:
            flash('Debes indicar quién resolvió el reporte', 'error')
            return redirect('/')
        
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("""
            UPDATE datos 
            SET estado = 'resuelto', resuelto_por = ?
            WHERE id = ?
        """, (resuelto_por, id_reporte))
        conn.commit()
        conn.close()
        
        flash(f'Reporte #{id_reporte} marcado como resuelto por {resuelto_por}', 'success')
        return redirect('/')
    except Exception as e:
        flash(f'Error al resolver reporte: {str(e)}', 'error')
        return redirect('/')

@app.route('/estadisticas')
def estadisticas():
    try:
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

        cur.execute("SELECT piso, COUNT(*) FROM datos GROUP BY piso ORDER BY COUNT(*) DESC")
        por_piso = cur.fetchall()

        cur.execute("""
            SELECT resuelto_por
            FROM datos 
            WHERE resuelto_por IS NOT NULL AND resuelto_por != ''
        """)
        
        contador_personas = {}
        for fila in cur.fetchall():
            resuelto_por = fila[0]
            personas = [p.strip() for p in resuelto_por.split(',')]
            for persona in personas:
                if persona:
                    contador_personas[persona] = contador_personas.get(persona, 0) + 1
        
        top_resueltos = sorted(contador_personas.items(), key=lambda x: x[1], reverse=True)[:5]

        cur.execute("""
            SELECT COUNT(DISTINCT substr(fecha, 4, 2) || '/' || substr(fecha, 7, 2)) as meses_unicos
            FROM datos
            WHERE NOT (
                (substr(fecha, 4, 2) = '08' AND CAST(substr(fecha, 1, 2) AS INTEGER) >= 7) OR
                (substr(fecha, 4, 2) = '09' AND CAST(substr(fecha, 1, 2) AS INTEGER) <= 30)
            )
        """)
        meses_unicos = cur.fetchone()[0]
        
        if meses_unicos == 0:
            cur.execute("""
                SELECT COUNT(DISTINCT substr(fecha, 4, 2) || '/' || substr(fecha, 7, 2)) as meses_unicos
                FROM datos
            """)
            meses_unicos = cur.fetchone()[0]
        
        promedio_mes = round(total / meses_unicos, 2) if meses_unicos > 0 else 0
        semanas_totales = meses_unicos * 4.33 if meses_unicos > 0 else 1
        promedio_semana = round(total / semanas_totales, 2) if semanas_totales > 0 else 0

        # ESTADÍSTICAS TEMPORALES
        meses_es = {
            '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
            '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
            '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
        }
        
        cur.execute("SELECT fecha FROM datos WHERE fecha IS NOT NULL AND fecha != ''")
        fechas_raw = cur.fetchall()
        
        datos_dias = []
        datos_meses = []
        
        for (fecha_str,) in fechas_raw:
            try:
                fecha_obj = datetime.strptime(fecha_str, '%d/%m/%y')
                fecha_display = fecha_obj.strftime('%d/%m/%Y')
                datos_dias.append((fecha_obj, fecha_display))
                
                mes_num = fecha_obj.strftime('%m')
                año = fecha_obj.strftime('%Y')
                mes_nombre = meses_es.get(mes_num, mes_num)
                mes_display = f"{mes_nombre} {año}"
                datos_meses.append((fecha_obj, mes_display))
            except (ValueError, AttributeError):
                continue
        
        contador_dias = defaultdict(int)
        for fecha_obj, fecha_display in datos_dias:
            contador_dias[fecha_display] += 1
        
        dias_ordenados = sorted(
            contador_dias.items(),
            key=lambda x: datetime.strptime(x[0], '%d/%m/%Y'),
            reverse=False
        )
        
        contador_meses = defaultdict(int)
        fecha_por_mes = {}
        
        for fecha_obj, mes_display in datos_meses:
            contador_meses[mes_display] += 1
            if mes_display not in fecha_por_mes:
                fecha_por_mes[mes_display] = fecha_obj
        
        meses_ordenados = sorted(
            contador_meses.items(),
            key=lambda x: fecha_por_mes[x[0]],
            reverse=False
        )

        conn.close()

        # Convertir a JSON como listas
        por_dia_json = json.dumps(dias_ordenados)
        por_mes_json = json.dumps(meses_ordenados)

        return render_template(
            'estadisticas.html',
            total=total,
            por_estado=por_estado,
            por_oficina=por_oficina,
            por_piso=por_piso,
            top_resueltos=top_resueltos,
            promedio_mes=promedio_mes,
            promedio_semana=promedio_semana,
            meses_activos=meses_unicos,
            por_dia=por_dia_json,
            por_mes=por_mes_json
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error al cargar estadísticas: {str(e)}", 500

@app.route('/api/estadisticas/tendencias')
def api_tendencias():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                substr(fecha, 4, 2) || '/' || substr(fecha, 7, 2) as mes,
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'resuelto' THEN 1 ELSE 0 END) as resueltos,
                SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'en proceso' THEN 1 ELSE 0 END) as en_proceso
            FROM datos
            GROUP BY mes
            ORDER BY substr(fecha, 7, 2) DESC, substr(fecha, 4, 2) DESC
            LIMIT 12
        """)
        
        resultados = cur.fetchall()
        conn.close()
        
        data = {
            'labels': [r[0] for r in reversed(resultados)],
            'datasets': [
                {
                    'label': 'Total',
                    'data': [r[1] for r in reversed(resultados)],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                },
                {
                    'label': 'Resueltos',
                    'data': [r[2] for r in reversed(resultados)],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.1)',
                },
                {
                    'label': 'Pendientes',
                    'data': [r[3] for r in reversed(resultados)],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.1)',
                },
                {
                    'label': 'En Proceso',
                    'data': [r[4] for r in reversed(resultados)],
                    'borderColor': 'rgb(255, 205, 86)',
                    'backgroundColor': 'rgba(255, 205, 86, 0.1)',
                }
            ]
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ultima_actualizacion')
def ultima_actualizacion():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT MAX(id) as ultimo_id, 
                   COUNT(*) as total,
                   MAX(fecha) as ultima_fecha
            FROM datos
        """)
        resultado = cur.fetchone()
        conn.close()
        
        return jsonify({
            'ultimo_id': resultado[0] if resultado[0] else 0,
            'total': resultado[1] if resultado[1] else 0,
            'ultima_fecha': resultado[2] if resultado[2] else ''
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/actualizar', methods=['GET', 'POST'])
def actualizar_estado():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if request.method == 'POST':
            id_reporte = request.form['id_reporte']
            resuelto_por = request.form.get('resuelto_por', '').strip()

            if resuelto_por:
                cur.execute("""
                    UPDATE datos 
                    SET estado = 'resuelto', resuelto_por = ?
                    WHERE id = ?
                """, (resuelto_por, id_reporte))
                conn.commit()
                flash(f'Reporte #{id_reporte} marcado como resuelto', 'success')

        cur.execute("""
            SELECT id, piso, oficina, quien, razon, estado, fecha 
            FROM datos 
            WHERE estado IN ('pendiente', 'en proceso')
            ORDER BY id DESC
        """)
        reportes = cur.fetchall()
        conn.close()
        return render_template('actualizar.html', reportes=reportes)
    except Exception as e:
        return f"Error al actualizar: {str(e)}", 500

@app.route('/excel')
def generar_excel():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT * FROM datos ORDER BY id DESC")
        filas = cur.fetchall()
        conn.close()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reportes"
        ws.append(['ID', 'Piso', 'Oficina', 'Quién', 'Razón', 'Estado', 'Fecha', 'Resuelto por'])

        for f in filas:
            ws.append(f)

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min((max_length + 2), 50)
            ws.column_dimensions[column].width = adjusted_width

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f'reportes_{fecha_actual}.xlsx'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return f"Error al generar Excel: {str(e)}", 500

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_reporte(id):
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("DELETE FROM datos WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        flash(f'Reporte #{id} eliminado exitosamente', 'success')
        return redirect('/')
    except Exception as e:
        flash(f'Error al eliminar reporte: {str(e)}', 'error')
        return redirect('/')

@app.route('/debugdb')
def debugdb():
    info = f"""
    <h3>Información de Base de Datos</h3>
    <p><b>BD Local (Reportes):</b> {DB_PATH}</p>
    <p><b>BD Remota (Oficinas):</b> {DB_OFICINAS_PATH}</p>
    """
    
    conn_oficinas = obtener_conexion_oficinas()
    if conn_oficinas:
        try:
            cur = conn_oficinas.cursor()
            cur.execute("SELECT COUNT(*) FROM oficinas")
            count = cur.fetchone()[0]
            info += f"<p><b>Oficinas en BD remota:</b> {count}</p>"
            conn_oficinas.close()
        except:
            info += "<p style='color:red;'><b>Error al leer oficinas de BD remota</b></p>"
    else:
        info += "<p style='color:red;'><b>No se pudo conectar a BD remota de oficinas</b></p>"
    
    return info

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host="16.1.1.118", port=port)