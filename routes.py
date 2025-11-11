"""
Rutas de Flask
"""
from flask import render_template, request, redirect, send_file, flash, jsonify
from datetime import datetime, timedelta
from io import BytesIO
import openpyxl
import json
from collections import defaultdict

from database import obtener_conexion, obtener_conexion_oficinas
from utils import normalizar_nombre, dividir_nombres
from config import EMPLEADOS


def parse_fecha_flexible(s):
    """Intenta interpretar distintos formatos de fecha"""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None

def registrar_rutas(app):
    """Registra todas las rutas de Flask"""
    
    @app.route('/')
    def index():
        try:
            conn = obtener_conexion()
            cur = conn.cursor()
            
            filtro_estado = request.args.get('estado', '')
            filtro_piso = request.args.get('piso', '')
            busqueda = request.args.get('busqueda', '')
            limite = request.args.get('limite', '50')
            pagina_actual = int(request.args.get('pagina', 1))
            
            query = "SELECT d.*, (SELECT COUNT(*) FROM comentarios WHERE reporte_id = d.id) as num_comentarios FROM datos d WHERE 1=1"
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
            
            query_total = "SELECT COUNT(*) FROM datos d WHERE 1=1"
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
            
            total_paginas = 1
            
            if limite != 'todos':
                try:
                    limite_num = int(limite)
                    total_paginas = (total_reportes + limite_num - 1) // limite_num
                    offset = (pagina_actual - 1) * limite_num
                    query += f" LIMIT {limite_num} OFFSET {offset}"
                except:
                    limite = '50'
            
            cur.execute(query, params)
            reportes = cur.fetchall()
            
            cur.execute("SELECT DISTINCT piso FROM datos ORDER BY piso")
            pisos_disponibles = [p[0] for p in cur.fetchall()]
            conn.close()
            
            return render_template('index.html', 
                                 reportes=reportes,
                                 total_reportes=total_reportes,
                                 pisos_disponibles=pisos_disponibles,
                                 filtro_estado=filtro_estado,
                                 filtro_piso=filtro_piso,
                                 busqueda=busqueda,
                                 limite=limite,
                                 pagina_actual=pagina_actual,
                                 total_paginas=total_paginas)
        except Exception as e:
            return f"Error: {str(e)}", 500

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
                
                # Obtener la fecha del reporte del campo fecha_reporte
                fecha = request.form.get('fecha_reporte', '').strip()
                
                # Si no hay fecha, usar la fecha actual
                if not fecha:
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
                flash(f'Error: {str(e)}', 'error')
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
            except:
                pass

        oficinas_json = json.dumps(oficinas_por_piso)
        return render_template('nuevo.html', oficinas_json=oficinas_json, empleados=EMPLEADOS)

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
                    fecha = request.form.get('fecha_resolucion', datetime.now().strftime("%d/%m/%y"))
                    cur.execute("""
                        UPDATE datos 
                        SET piso=?, oficina=?, quien=?, razon=?, estado=?, resuelto_por=?, fecha=?
                        WHERE id=?
                    """, (piso, oficina, quien, razon, estado, resuelto_por, fecha, id))
                else:
                    cur.execute("""
                        UPDATE datos 
                        SET piso=?, oficina=?, quien=?, razon=?, estado=?, resuelto_por=''
                        WHERE id=?
                    """, (piso, oficina, quien, razon, estado, id))
                
                conn.commit()
                conn.close()
                flash(f'Reporte #{id} actualizado', 'success')
                return redirect('/')
                
            except Exception as e:
                conn.close()
                flash(f'Error: {str(e)}', 'error')
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
            except:
                pass
        
        cur.execute("SELECT * FROM comentarios WHERE reporte_id = ? ORDER BY fecha DESC", (id,))
        comentarios = cur.fetchall()
        conn.close()
        
        oficinas_json = json.dumps(oficinas_por_piso)
        return render_template('editar.html', reporte=reporte, comentarios=comentarios, oficinas_json=oficinas_json, empleados=EMPLEADOS)

    @app.route('/comentario/<int:id>', methods=['POST'])
    def agregar_comentario(id):
        try:
            texto = request.form.get('comentario', '').strip()
            autor = request.form.get('autor', 'Anónimo').strip()
            
            if not texto:
                flash('El comentario no puede estar vacío', 'error')
                return redirect(f'/editar/{id}')
            
            conn = obtener_conexion()
            cur = conn.cursor()
            
            cur.execute("SELECT id FROM datos WHERE id = ?", (id,))
            if not cur.fetchone():
                flash(f'Reporte #{id} no encontrado', 'error')
                conn.close()
                return redirect('/')
            
            fecha = datetime.now().strftime("%d/%m/%y %H:%M")
            cur.execute("""
                INSERT INTO comentarios (reporte_id, texto, autor, fecha)
                VALUES (?, ?, ?, ?)
            """, (id, texto, autor, fecha))
            
            conn.commit()
            conn.close()
            
            flash('Comentario agregado', 'success')
            return redirect(f'/editar/{id}')
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(f'/editar/{id}')

    @app.route('/estadisticas')
    def estadisticas():
        try:
            conn = obtener_conexion()
            cur = conn.cursor()

            # ==============================
            # Totales generales
            # ==============================
            cur.execute("SELECT COUNT(*) FROM datos")
            total = cur.fetchone()[0]

            # Por estado
            cur.execute("SELECT estado, COUNT(*) FROM datos GROUP BY estado")
            por_estado = cur.fetchall()

            # Top oficinas (top 5)
            cur.execute("""
                SELECT oficina, COUNT(*) as total 
                FROM datos 
                GROUP BY oficina 
                ORDER BY total DESC 
                LIMIT 5
            """)
            por_oficina = cur.fetchall()

            # Por piso (top 5)
            cur.execute("""
                SELECT piso, COUNT(*) as total 
                FROM datos 
                GROUP BY piso 
                ORDER BY total DESC, piso ASC
                LIMIT 5
            """)
            por_piso = cur.fetchall()

            # ==============================
            # Ranking "resuelto_por" (1 punto por persona) - general
            # ==============================
            cur.execute("""
                SELECT resuelto_por
                FROM datos 
                WHERE resuelto_por != '' AND resuelto_por IS NOT NULL
            """)
            resultados = cur.fetchall()

            empleados_contados = {}
            for (nombre_completo,) in resultados:
                for nombre in dividir_nombres(nombre_completo):
                    empleados_contados[nombre] = empleados_contados.get(nombre, 0) + 1

            top_resueltos = sorted(
                empleados_contados.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            # ==============================
            # Estadísticas por MES (conteo por MM/YY) para gráficos
            # ==============================
            cur.execute("""
                SELECT substr(fecha, 4, 2) || '/' || substr(fecha, 7, 2) AS mes, COUNT(*) AS total 
                FROM datos 
                GROUP BY mes
            """)
            por_mes_raw = cur.fetchall()  # [('03/25', 62), ('04/25', 51), ...]

            nombres_meses = {
                "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
                "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
                "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
            }

            # Orden cronológico y etiquetas legibles (para tu card de "Reportes por Mes")
            contador_meses = {}
            fecha_por_mes = {}
            for mes_raw, cant in por_mes_raw:
                try:
                    mm, yy = mes_raw.split('/')
                    anio_completo = f"20{yy}" if len(yy) == 2 else yy
                    fecha_obj = datetime.strptime(f"01/{mm}/{anio_completo}", "%d/%m/%Y")
                    contador_meses[mes_raw] = cant
                    fecha_por_mes[mes_raw] = fecha_obj
                except Exception:
                    continue

            meses_ordenados_raw = sorted(contador_meses.items(), key=lambda x: fecha_por_mes[x[0]])
            meses_ordenados_legibles = []
            for mes_raw, cant in meses_ordenados_raw:
                mm, yy = mes_raw.split('/')
                anio_completo = f"20{yy}" if len(yy) == 2 else yy
                etiqueta = f"{nombres_meses.get(mm, mm)} {anio_completo}"
                meses_ordenados_legibles.append((etiqueta, cant))

            # ==============================
            # Promedio mensual/semanal (estimado)
            # ==============================
            anios = set()
            for mes_raw, _ in por_mes_raw:
                try:
                    _, yy = mes_raw.split('/')
                    anios.add(yy)
                except:
                    pass
            yy_target = max(anios) if anios else datetime.now().strftime("%y")

            meses_validos = []
            for mes_raw, cant in por_mes_raw:
                try:
                    mm, yy = mes_raw.split('/')
                    if yy == yy_target and mm in {f"{i:02d}" for i in range(1, 13)}:
                        meses_validos.append((mm, cant))
                except:
                    pass

            meses_validos.sort(key=lambda x: int(x[0]))
            meses_validos = meses_validos[:12]

            sum_mes = sum(cant for _, cant in meses_validos)
            meses_unicos = len(meses_validos) if meses_validos else 1
            promedio_mes = round(sum_mes / meses_unicos) if meses_unicos > 0 else 0

            dias_trabajados = 21 * meses_unicos
            promedio_semana = round((sum_mes / dias_trabajados) * 5) if dias_trabajados > 0 else 0

            # ==============================
            # RANKING HISTÓRICO POR MES (GANADOR/ES DEL MES) - SOLO LUN–VIE
            # ==============================
            cur.execute("""
                SELECT resuelto_por, fecha
                FROM datos
                WHERE resuelto_por != '' AND resuelto_por IS NOT NULL
            """)
            todas_resoluciones = cur.fetchall()  # [(nombre_completo, 'dd/mm/yy'), ...]

            # Agrupar por mes 'YYYY-MM' contando por técnico solo lun-vie
            conteo_por_mes = {}  # 'YYYY-MM' -> {tecnico: count}
            for nombre_completo, fecha_txt in todas_resoluciones:
                f = parse_fecha_flexible(fecha_txt)
                if not f or f.weekday() >= 5:
                    continue
                clave_mes = f.strftime("%Y-%m")
                cont = conteo_por_mes.setdefault(clave_mes, {})
                for nombre in dividir_nombres(nombre_completo):
                    cont[nombre] = cont.get(nombre, 0) + 1

            # Orden cronológico
            meses_claves_ordenadas = sorted(conteo_por_mes.keys())

            # Ganadores por mes (puede haber empate) y ranking global de "meses ganados"
            ganadores_por_mes = {}   # 'YYYY-MM' -> [(nombre, count_max), ... empatados]
            conteo_meses_ganados = {}  # tecnico -> cantidad de meses ganados

            for clave in meses_claves_ordenadas:
                ranking = conteo_por_mes[clave]
                if not ranking:
                    ganadores_por_mes[clave] = []
                    continue
                max_val = max(ranking.values())
                winners = [(k, v) for k, v in ranking.items() if v == max_val]
                ganadores_por_mes[clave] = sorted(winners, key=lambda x: x[0].lower())  # orden alfabético estable
                # sumar 1 por mes ganado a cada ganador (si hubo empate, ambos suman 1 mes ganado)
                for k, _ in winners:
                    conteo_meses_ganados[k] = conteo_meses_ganados.get(k, 0) + 1

            # Navegable de meses para el template: [{clave:'YYYY-MM', etiqueta:'Mes Año', winners:[[nombre, n], ...]}]
            meses_ganadores_navegable = []
            for clave in meses_claves_ordenadas:
                anio, mes = clave.split('-')
                etiqueta = f"{nombres_meses.get(mes, mes)} {anio}"
                meses_ganadores_navegable.append({
                    "clave": clave,
                    "etiqueta": etiqueta,
                    "winners": ganadores_por_mes.get(clave, []),
                })

            # Top 3 global de “Ganadores del Mes”
            top3_ganadores_mes = sorted(conteo_meses_ganados.items(), key=lambda x: x[1], reverse=True)[:3]

            # ==============================
            # Estadísticas por DÍA (últimos 30, etiqueta dd/mm)
            # ==============================
            cur.execute("""
                SELECT fecha, COUNT(*) as total
                FROM datos
                GROUP BY fecha
                ORDER BY substr(fecha, 7, 2) DESC, substr(fecha, 4, 2) DESC, substr(fecha, 1, 2) DESC
                LIMIT 30
            """)
            por_dia = cur.fetchall()

            contador_dias = {}
            fecha_por_dia2 = {}
            for fecha_txt, cant in por_dia:
                f = parse_fecha_flexible(fecha_txt)
                if not f:
                    continue
                etiqueta = f.strftime("%d/%m")
                contador_dias[etiqueta] = cant
                fecha_por_dia2[etiqueta] = f

            dias_ordenados = sorted(contador_dias.items(), key=lambda x: fecha_por_dia2[x[0]])

            # ==============================
            # Cerrar conexión y preparar datos para renderizar
            # ==============================
            conn.close()

            por_dia_json = json.dumps(dias_ordenados, ensure_ascii=False)
            por_mes_json = json.dumps(meses_ordenados_legibles, ensure_ascii=False)

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
                por_mes=por_mes_json,

                # Datos para "Ganador del mes" navegable y Top 3 global
                meses_ganadores_navegable=json.dumps(meses_ganadores_navegable, ensure_ascii=False),
                top3_ganadores_mes=top3_ganadores_mes,
            )

        except Exception as e:
            return f"Error: {str(e)}", 500




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
                    {'label': 'Total', 'data': [r[1] for r in reversed(resultados)], 'borderColor': 'rgb(54, 162, 235)', 'backgroundColor': 'rgba(54, 162, 235, 0.1)'},
                    {'label': 'Resueltos', 'data': [r[2] for r in reversed(resultados)], 'borderColor': 'rgb(75, 192, 192)', 'backgroundColor': 'rgba(75, 192, 192, 0.1)'},
                    {'label': 'Pendientes', 'data': [r[3] for r in reversed(resultados)], 'borderColor': 'rgb(255, 99, 132)', 'backgroundColor': 'rgba(255, 99, 132, 0.1)'},
                    {'label': 'En Proceso', 'data': [r[4] for r in reversed(resultados)], 'borderColor': 'rgb(255, 205, 86)', 'backgroundColor': 'rgba(255, 205, 86, 0.1)'}
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
            cur.execute("SELECT MAX(id) as ultimo_id, COUNT(*) as total, MAX(fecha) as ultima_fecha FROM datos")
            resultado = cur.fetchone()
            conn.close()
            return jsonify({'ultimo_id': resultado[0] if resultado[0] else 0, 'total': resultado[1] if resultado[1] else 0, 'ultima_fecha': resultado[2] if resultado[2] else ''})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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

    @app.route('/actualizar', methods=['GET', 'POST'])
    def actualizar_estado_web():
        try:
            conn = obtener_conexion()
            cur = conn.cursor()

            if request.method == 'POST':
                id_reporte = request.form['id_reporte']
                resuelto_por = request.form.get('resuelto_por', '').strip()
                fecha = request.form.get('fecha_resolucion', datetime.now().strftime("%d/%m/%y"))

                if resuelto_por:
                    cur.execute("UPDATE datos SET estado = 'resuelto', resuelto_por = ?, fecha = ? WHERE id = ?", (resuelto_por, fecha, id_reporte))
                    conn.commit()
                    flash(f'Reporte #{id_reporte} marcado como resuelto', 'success')

            cur.execute("SELECT id, piso, oficina, quien, razon, estado, fecha FROM datos WHERE estado IN ('pendiente', 'en proceso') ORDER BY id DESC")
            reportes = cur.fetchall()
            conn.close()
            return render_template('actualizar.html', reportes=reportes, empleados=EMPLEADOS)
        except Exception as e:
            return f"Error: {str(e)}", 500

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

            return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except Exception as e:
            return f"Error: {str(e)}", 500

    @app.route('/eliminar/<int:id>', methods=['POST'])
    def eliminar_reporte(id):
        try:
            conn = obtener_conexion()
            cur = conn.cursor()
            cur.execute("DELETE FROM datos WHERE id = ?", (id,))
            conn.commit()
            conn.close()
            flash(f'Reporte #{id} eliminado', 'success')
            return redirect('/')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect('/')

    @app.route('/debugdb')
    def debugdb():
        from config import DB_PATH, DB_OFICINAS_PATH
        from telegram_bot import telegram_bot
        
        info = f"<h3>Info BD</h3><p>Local: {DB_PATH}</p><p>Remota: {DB_OFICINAS_PATH}</p>"
        conn_oficinas = obtener_conexion_oficinas()
        if conn_oficinas:
            try:
                cur = conn_oficinas.cursor()
                cur.execute("SELECT COUNT(*) FROM oficinas")
                count = cur.fetchone()[0]
                info += f"<p>Oficinas: {count}</p>"
                conn_oficinas.close()
            except:
                info += "<p style='color:red;'>Error BD oficinas</p>"
        else:
            info += "<p style='color:red;'>No conecta BD oficinas</p>"
        
        info += "<hr><h3>Bot</h3>"
        if telegram_bot:
            info += "<p style='color:green;'>✅ Bot activo</p>"
        else:
            info += "<p style='color:orange;'>⚠️ Bot no iniciado</p>"
        
        return info
