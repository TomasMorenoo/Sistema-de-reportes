"""
Generación de reportes para Telegram
"""
from datetime import datetime
from database import obtener_conexion
from utils import normalizar_nombre

def generar_reporte_texto(tipo='general'):
    """Genera un reporte en formato texto para Telegram"""
    conn = obtener_conexion()
    cur = conn.cursor()
    
    try:
        if tipo == 'general':
            return _generar_reporte_general(cur)
        elif tipo == 'pendientes':
            return _generar_reporte_pendientes(cur)
        elif tipo == 'hoy':
            return _generar_reporte_hoy(cur)
        elif tipo == 'semana':
            return _generar_reporte_semana(cur)
        elif tipo == 'estadisticas':
            return _generar_estadisticas(cur)
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        conn.close()

def _generar_reporte_general(cur):
    cur.execute("SELECT COUNT(*) FROM datos")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT estado, COUNT(*) FROM datos GROUP BY estado")
    por_estado = dict(cur.fetchall())
    
    cur.execute("""
        SELECT piso, COUNT(*) 
        FROM datos 
        GROUP BY piso 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    por_piso = cur.fetchall()
    
    reporte = f"📊 *REPORTE GENERAL DE TICKETS*\n\n"
    reporte += f"📈 Total de reportes: *{total}*\n\n"
    reporte += f"🔴 Pendientes: *{por_estado.get('pendiente', 0)}*\n"
    reporte += f"🟡 En proceso: *{por_estado.get('en proceso', 0)}*\n"
    reporte += f"🟢 Resueltos: *{por_estado.get('resuelto', 0)}*\n\n"
    
    if por_piso:
        reporte += f"🏢 *Top 5 Pisos con más reportes:*\n"
        for piso, count in por_piso:
            reporte += f"  • Piso {piso}: {count} reportes\n"
    
    return reporte

def _generar_reporte_pendientes(cur):
    cur.execute("""
        SELECT id, piso, oficina, quien, razon, fecha
        FROM datos 
        WHERE estado = 'pendiente'
        ORDER BY id DESC
        LIMIT 10
    """)
    pendientes = cur.fetchall()
    
    reporte = f"🔴 *REPORTES PENDIENTES* ({len(pendientes)})\n\n"
    
    if not pendientes:
        reporte += "✅ ¡No hay reportes pendientes!"
    else:
        for ticket in pendientes:
            reporte += f"🎫 *Ticket #{ticket[0]}*\n"
            reporte += f"📍 Piso {ticket[1]} - {ticket[2]}\n"
            reporte += f"👤 {ticket[3]}\n"
            reporte += f"📝 {ticket[4][:50]}...\n"
            reporte += f"📅 {ticket[5]}\n"
            reporte += "─" * 30 + "\n\n"
    
    return reporte

def _generar_reporte_hoy(cur):
    fecha_hoy = datetime.now().strftime("%d/%m/%y")
    
    cur.execute("SELECT COUNT(*) FROM datos WHERE fecha = ?", (fecha_hoy,))
    total_hoy = cur.fetchone()[0]
    
    cur.execute("""
        SELECT id, piso, oficina, quien, razon, estado, resuelto_por
        FROM datos 
        WHERE fecha = ?
        ORDER BY id DESC
    """, (fecha_hoy,))
    reportes_hoy = cur.fetchall()
    
    reporte = f"📅 *REPORTES DE HOY* ({fecha_hoy})\n\nTotal: *{total_hoy}* reportes\n\n"
    
    if not reportes_hoy:
        reporte += "No hay reportes registrados hoy."
    else:
        for ticket in reportes_hoy:
            estado_emoji = {"pendiente": "🔴", "en proceso": "🟡", "resuelto": "🟢"}
            reporte += f"{estado_emoji.get(ticket[5], '⚪')} *#{ticket[0]}* - Piso {ticket[1]}\n"
            reporte += f"  {ticket[2]} | {ticket[3]}\n"
            reporte += f"  {ticket[4][:40]}...\n"
            
            if ticket[5] == 'resuelto' and ticket[6]:
                reporte += f"  ✅ Resuelto por: *{ticket[6]}*\n"
            
            reporte += "\n"
    
    return reporte

def _generar_reporte_semana(cur):
    cur.execute("""
        SELECT COUNT(*) FROM datos 
        WHERE DATE(substr(fecha, 7, 2) || '-' || substr(fecha, 4, 2) || '-20' || substr(fecha, 1, 2)) 
        >= DATE('now', '-7 days')
    """)
    total_semana = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM datos")
    total = cur.fetchone()[0]
    
    cur.execute("""
        SELECT estado, COUNT(*) 
        FROM datos 
        WHERE DATE(substr(fecha, 7, 2) || '-' || substr(fecha, 4, 2) || '-20' || substr(fecha, 1, 2)) 
        >= DATE('now', '-7 days')
        GROUP BY estado
    """)
    por_estado = dict(cur.fetchall())
    
    # Obtener empleados de la semana - cada persona recibe 1 punto por trabajo
    cur.execute("""
        SELECT resuelto_por
        FROM datos 
        WHERE resuelto_por != '' 
        AND resuelto_por IS NOT NULL
        AND estado = 'resuelto'
        AND DATE(substr(fecha, 7, 2) || '-' || substr(fecha, 4, 2) || '-20' || substr(fecha, 1, 2)) 
        >= DATE('now', '-7 days')
    """)
    resultados = cur.fetchall()
    
    from utils import dividir_nombres
    empleados_contados = {}
    
    for (nombre_completo,) in resultados:
        nombres = dividir_nombres(nombre_completo)
        # Cada persona recibe 1 punto completo
        for nombre in nombres:
            if nombre in empleados_contados:
                empleados_contados[nombre] += 1
            else:
                empleados_contados[nombre] = 1
    
    # Obtener el empleado con más puntos
    empleado_semana = None
    if empleados_contados:
        empleado_semana = max(empleados_contados.items(), key=lambda x: x[1])
    
    reporte = f"📊 *REPORTE SEMANAL*\n(Últimos 7 días)\n\n"
    reporte += f"📈 Total esta semana: *{total_semana}*\n"
    reporte += f"📊 Total histórico: *{total}*\n\n"
    reporte += f"🔴 Pendientes: *{por_estado.get('pendiente', 0)}*\n"
    reporte += f"🟡 En proceso: *{por_estado.get('en proceso', 0)}*\n"
    reporte += f"🟢 Resueltos: *{por_estado.get('resuelto', 0)}*\n\n"
    
    if empleado_semana:
        reporte += f"🏆 *EMPLEADO DE LA SEMANA*\n"
        reporte += f"👤 {empleado_semana[0]}\n"
        reporte += f"✅ {int(empleado_semana[1])} trabajos\n"
    
    return reporte

def _generar_estadisticas(cur):
    cur.execute("SELECT COUNT(*) FROM datos")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT estado, COUNT(*) FROM datos GROUP BY estado")
    por_estado = dict(cur.fetchall())
    
    cur.execute("""
        SELECT oficina, COUNT(*) as total 
        FROM datos 
        GROUP BY oficina 
        ORDER BY total DESC 
        LIMIT 5
    """)
    top_oficinas = cur.fetchall()
    
    # Obtener todos los registros con resuelto_por
    cur.execute("""
        SELECT resuelto_por
        FROM datos 
        WHERE resuelto_por != '' AND resuelto_por IS NOT NULL
    """)
    resultados = cur.fetchall()
    
    # Contar: cada persona recibe 1 punto por cada trabajo, sin importar cuántas personas participaron
    from utils import dividir_nombres
    empleados_contados = {}
    
    for (nombre_completo,) in resultados:
        nombres = dividir_nombres(nombre_completo)
        # Cada persona recibe 1 punto completo
        for nombre in nombres:
            if nombre in empleados_contados:
                empleados_contados[nombre] += 1
            else:
                empleados_contados[nombre] = 1
    
    # Ordenar y obtener top 5
    top_resueltos = sorted(empleados_contados.items(), key=lambda x: x[1], reverse=True)[:5]
    
    cur.execute("SELECT COUNT(DISTINCT substr(fecha, 4, 5)) FROM datos")
    meses = cur.fetchone()[0] or 1
    promedio_mes = total / meses
    
    reporte = f"📊 *ESTADÍSTICAS COMPLETAS*\n\n"
    reporte += f"📈 Total histórico: *{total}*\n"
    reporte += f"📊 Promedio mensual: *{promedio_mes:.1f}*\n\n"
    reporte += f"*Estado actual:*\n"
    reporte += f"🔴 Pendientes: {por_estado.get('pendiente', 0)}\n"
    reporte += f"🟡 En proceso: {por_estado.get('en proceso', 0)}\n"
    reporte += f"🟢 Resueltos: {por_estado.get('resuelto', 0)}\n\n"
    
    if top_oficinas:
        reporte += f"🏢 *Top 5 Oficinas:*\n"
        for i, (oficina, count) in enumerate(top_oficinas, 1):
            reporte += f"{i}. {oficina}: {count} reportes\n"
        reporte += "\n"
    
    if top_resueltos:
        reporte += f"🏆 *Top 5 Empleados:*\n"
        for i, (empleado, puntos) in enumerate(top_resueltos, 1):
            reporte += f"{i}. {empleado}: {int(puntos)} trabajos\n"
    
    return reporte
