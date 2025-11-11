"""
Bot de Telegram - Comandos y handlers
VERSIÓN MEJORADA: Compatible con threads y previene múltiples instancias
"""
import os
import sys
import asyncio
import tempfile
import threading
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from telegram.error import Conflict
import openpyxl

from config import (
    TELEGRAM_TOKEN, PISO, OFICINA, QUIEN, RAZON, ESTADO, 
    RESUELTO_POR, FECHA_RESOLUCION, ACTUALIZAR_ID, ACTUALIZAR_ESTADO,
    ACTUALIZAR_RESUELTO_POR, ACTUALIZAR_FECHA, EMPLEADOS
)
from database import (
    obtener_conexion, obtener_pisos_disponibles, obtener_oficinas_por_piso
)
from reportes import generar_reporte_texto

telegram_bot = None
_application = None
_shutdown_event = None

# ==================== COMANDOS SIMPLES ====================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """🤖 *Bot de Reportes CNE*

*📊 Comandos de Consulta:*
/reporte - Estadísticas generales
/estadisticas - Estadísticas detalladas
/pendientes - Ver reportes pendientes
/hoy - Reportes de hoy
/semana - Reporte semanal
/excel - Descargar Excel

*✏️ Comandos de Acción:*
/nuevo - Crear nuevo reporte
/actualizar - Actualizar estado

*ℹ️ Ayuda:*
/help - Mostrar ayuda"""
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)

async def cmd_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporte = generar_reporte_texto('general')
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def cmd_estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporte = generar_reporte_texto('estadisticas')
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def cmd_pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporte = generar_reporte_texto('pendientes')
    if len(reporte) > 4000:
        partes = [reporte[i:i+4000] for i in range(0, len(reporte), 4000)]
        for parte in partes:
            await update.message.reply_text(parte, parse_mode='Markdown')
    else:
        await update.message.reply_text(reporte, parse_mode='Markdown')

async def cmd_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporte = generar_reporte_texto('hoy')
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def cmd_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reporte = generar_reporte_texto('semana')
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def cmd_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp:
            nombre_archivo = tmp.name
            wb.save(nombre_archivo)

        with open(nombre_archivo, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f'reportes_{fecha_actual}.xlsx',
                caption=f"📊 Reporte completo\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
        
        os.remove(nombre_archivo)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ==================== CREAR NUEVO REPORTE ====================

async def cmd_nuevo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pisos = obtener_pisos_disponibles()
    keyboard = [[piso] for piso in pisos]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "📝 *CREAR NUEVO REPORTE*\n\nPaso 1/6: Selecciona el piso:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return PISO

async def nuevo_piso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['piso'] = update.message.text
    oficinas = obtener_oficinas_por_piso(context.user_data['piso'])
    
    if oficinas:
        keyboard = [[oficina] for oficina in oficinas[:10]]
        keyboard.append(['Otra oficina'])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Piso: *{context.user_data['piso']}*\n\nPaso 2/6: Selecciona la oficina:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"Piso: *{context.user_data['piso']}*\n\nPaso 2/6: Escribe el nombre de la oficina:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
    
    return OFICINA

async def nueva_oficina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['oficina'] = update.message.text
    await update.message.reply_text(
        f"Oficina: *{context.user_data['oficina']}*\n\nPaso 3/6: ¿Quién reporta?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    return QUIEN

async def nuevo_quien(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quien'] = update.message.text
    await update.message.reply_text(
        f"Reportado por: *{context.user_data['quien']}*\n\nPaso 4/6: Describe el problema:",
        parse_mode='Markdown'
    )
    return RAZON

async def nueva_razon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['razon'] = update.message.text
    keyboard = [['pendiente'], ['en proceso'], ['resuelto']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Problema: *{context.user_data['razon'][:50]}...*\n\nPaso 5/6: Selecciona el estado:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ESTADO

async def nuevo_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['estado'] = update.message.text
    
    if context.user_data['estado'] == 'resuelto':
        keyboard = [[emp] for emp in EMPLEADOS]
        keyboard.append(['Otro'])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "Paso 6a/6: ¿Quién resolvió?",
            reply_markup=reply_markup
        )
        return RESUELTO_POR
    else:
        context.user_data['resuelto_por'] = ''
        context.user_data['fecha'] = datetime.now().strftime("%d/%m/%y")
        return await guardar_nuevo_reporte(update, context)

async def nuevo_resuelto_por(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['resuelto_por'] = update.message.text
    keyboard = [['Hoy'], ['Ayer'], ['Otra fecha']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Paso 6b/6: ¿Cuándo se resolvió?",
        reply_markup=reply_markup
    )
    return FECHA_RESOLUCION

async def nueva_fecha_resolucion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    respuesta = update.message.text
    
    if respuesta == 'Hoy':
        context.user_data['fecha'] = datetime.now().strftime("%d/%m/%y")
    elif respuesta == 'Ayer':
        ayer = datetime.now() - timedelta(days=1)
        context.user_data['fecha'] = ayer.strftime("%d/%m/%y")
    else:
        await update.message.reply_text(
            "Escribe la fecha (DD/MM/AA):",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data['esperando_fecha'] = True
        return FECHA_RESOLUCION
    
    return await guardar_nuevo_reporte(update, context)

async def guardar_nuevo_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('esperando_fecha'):
        context.user_data['fecha'] = update.message.text
        context.user_data.pop('esperando_fecha', None)
    
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO datos (piso, oficina, quien, razon, estado, fecha, resuelto_por)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            context.user_data['piso'],
            context.user_data['oficina'],
            context.user_data['quien'],
            context.user_data['razon'],
            context.user_data['estado'],
            context.user_data.get('fecha', ''),
            context.user_data.get('resuelto_por', '')
        ))
        
        conn.commit()
        ticket_id = cur.lastrowid
        conn.close()
        
        mensaje = f"""✅ *¡Reporte creado!*

📋 Ticket #*{ticket_id}*
🏢 Piso: {context.user_data['piso']}
🚪 Oficina: {context.user_data['oficina']}
👤 Reportado por: {context.user_data['quien']}
📝 Problema: {context.user_data['razon'][:100]}
📊 Estado: {context.user_data['estado']}"""
        
        if context.user_data['estado'] == 'resuelto':
            mensaje += f"\n✔️ Resuelto por: {context.user_data.get('resuelto_por', '')}"
            mensaje += f"\n📅 Fecha: {context.user_data.get('fecha', '')}"
        
        await update.message.reply_text(mensaje, reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al guardar: {str(e)}", reply_markup=ReplyKeyboardRemove())
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancelar_nuevo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Reporte cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ==================== ACTUALIZAR REPORTE ====================

async def cmd_actualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = obtener_conexion()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, piso, oficina, quien, razon, estado 
        FROM datos 
        WHERE estado != 'resuelto'
        ORDER BY id DESC 
        LIMIT 10
    """)
    reportes = cur.fetchall()
    conn.close()
    
    if not reportes:
        await update.message.reply_text("ℹ️ No hay reportes pendientes")
        return ConversationHandler.END
    
    mensaje = "📋 *ACTUALIZAR REPORTE*\n\nÚltimos reportes pendientes:\n\n"
    for r in reportes:
        mensaje += f"🎫 *#{r[0]}* [{r[5]}]\n"
        mensaje += f"  {r[1]} - {r[2]} | {r[3]}\n"
        mensaje += f"  {r[4][:35]}...\n\n"
    
    mensaje += "Escribe el *ID*:"
    await update.message.reply_text(mensaje, parse_mode='Markdown')
    return ACTUALIZAR_ID

async def actualizar_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticket_id = int(update.message.text)
        
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT * FROM datos WHERE id = ?", (ticket_id,))
        reporte = cur.fetchone()
        conn.close()
        
        if not reporte:
            await update.message.reply_text(f"❌ No existe #{ticket_id}")
            return ACTUALIZAR_ID
        
        context.user_data['actualizar_id'] = ticket_id
        keyboard = [['pendiente'], ['en proceso'], ['resuelto']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"📝 Ticket #*{ticket_id}*\nEstado actual: *{reporte[5]}*\n\nNuevo estado:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return ACTUALIZAR_ESTADO
        
    except ValueError:
        await update.message.reply_text("❌ Escribe solo el número del ID")
        return ACTUALIZAR_ID

async def actualizar_estado_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['actualizar_estado'] = update.message.text
    
    if context.user_data['actualizar_estado'] == 'resuelto':
        keyboard = [[emp] for emp in EMPLEADOS]
        keyboard.append(['Otro'])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text("¿Quién resolvió?", reply_markup=reply_markup)
        return ACTUALIZAR_RESUELTO_POR
    else:
        context.user_data['actualizar_resuelto_por'] = ''
        context.user_data['actualizar_fecha'] = ''
        return await guardar_actualizacion(update, context)

async def actualizar_resuelto_por_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['actualizar_resuelto_por'] = update.message.text
    keyboard = [['Hoy'], ['Ayer'], ['Otra fecha']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text("¿Cuándo se resolvió?", reply_markup=reply_markup)
    return ACTUALIZAR_FECHA

async def actualizar_fecha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    respuesta = update.message.text
    
    if respuesta == 'Hoy':
        context.user_data['actualizar_fecha'] = datetime.now().strftime("%d/%m/%y")
    elif respuesta == 'Ayer':
        ayer = datetime.now() - timedelta(days=1)
        context.user_data['actualizar_fecha'] = ayer.strftime("%d/%m/%y")
    else:
        await update.message.reply_text("Escribe fecha DD/MM/AA:", reply_markup=ReplyKeyboardRemove())
        context.user_data['esperando_fecha_act'] = True
        return ACTUALIZAR_FECHA
    
    return await guardar_actualizacion(update, context)

async def guardar_actualizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('esperando_fecha_act'):
        context.user_data['actualizar_fecha'] = update.message.text
        context.user_data.pop('esperando_fecha_act', None)
    
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        
        ticket_id = context.user_data['actualizar_id']
        nuevo_estado = context.user_data['actualizar_estado']
        resuelto_por = context.user_data.get('actualizar_resuelto_por', '')
        fecha = context.user_data.get('actualizar_fecha', '')
        
        if nuevo_estado == 'resuelto' and fecha:
            cur.execute("""
                UPDATE datos 
                SET estado = ?, resuelto_por = ?, fecha = ?
                WHERE id = ?
            """, (nuevo_estado, resuelto_por, fecha, ticket_id))
        elif nuevo_estado == 'resuelto':
            cur.execute("""
                UPDATE datos 
                SET estado = ?, resuelto_por = ?
                WHERE id = ?
            """, (nuevo_estado, resuelto_por, ticket_id))
        else:
            cur.execute("""
                UPDATE datos 
                SET estado = ?, resuelto_por = ''
                WHERE id = ?
            """, (nuevo_estado, ticket_id))
        
        conn.commit()
        conn.close()
        
        mensaje = f"✅ *Ticket #{ticket_id} actualizado!*\n\nNuevo estado: *{nuevo_estado}*\n"
        if nuevo_estado == 'resuelto' and resuelto_por:
            mensaje += f"Resuelto por: *{resuelto_por}*\n"
            if fecha:
                mensaje += f"Fecha: {fecha}"
        
        await update.message.reply_text(mensaje, reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}", reply_markup=ReplyKeyboardRemove())
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancelar_actualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ==================== INICIALIZAR BOT ====================

def iniciar_bot_telegram():
    """Inicia el bot de Telegram con protección contra múltiples instancias"""
    global telegram_bot, _application, _shutdown_event
    
    async def run_bot():
        global telegram_bot, _application, _shutdown_event
        
        # Crear evento de shutdown para este thread
        _shutdown_event = asyncio.Event()
        
        try:
            print("🚀 Iniciando bot de Telegram...")
            
            # Crear aplicación
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            _application = application
            
            # Comandos simples
            application.add_handler(CommandHandler("start", cmd_start))
            application.add_handler(CommandHandler("help", cmd_help))
            application.add_handler(CommandHandler("reporte", cmd_reporte))
            application.add_handler(CommandHandler("estadisticas", cmd_estadisticas))
            application.add_handler(CommandHandler("pendientes", cmd_pendientes))
            application.add_handler(CommandHandler("hoy", cmd_hoy))
            application.add_handler(CommandHandler("semana", cmd_semana))
            application.add_handler(CommandHandler("excel", cmd_excel))
            
            # ConversationHandler para crear
            conv_nuevo = ConversationHandler(
                entry_points=[CommandHandler('nuevo', cmd_nuevo)],
                states={
                    PISO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_piso)],
                    OFICINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, nueva_oficina)],
                    QUIEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_quien)],
                    RAZON: [MessageHandler(filters.TEXT & ~filters.COMMAND, nueva_razon)],
                    ESTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_estado)],
                    RESUELTO_POR: [MessageHandler(filters.TEXT & ~filters.COMMAND, nuevo_resuelto_por)],
                    FECHA_RESOLUCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, nueva_fecha_resolucion)],
                },
                fallbacks=[CommandHandler('cancelar', cancelar_nuevo)]
            )
            application.add_handler(conv_nuevo)
            
            # ConversationHandler para actualizar
            conv_actualizar = ConversationHandler(
                entry_points=[CommandHandler('actualizar', cmd_actualizar)],
                states={
                    ACTUALIZAR_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, actualizar_id)],
                    ACTUALIZAR_ESTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, actualizar_estado_handler)],
                    ACTUALIZAR_RESUELTO_POR: [MessageHandler(filters.TEXT & ~filters.COMMAND, actualizar_resuelto_por_handler)],
                    ACTUALIZAR_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, actualizar_fecha_handler)],
                },
                fallbacks=[CommandHandler('cancelar', cancelar_actualizar)]
            )
            application.add_handler(conv_actualizar)
            
            telegram_bot = application.bot
            
            print("✅ Bot de Telegram iniciado correctamente")
            print("📱 Esperando mensajes...")
            
            # Inicializar y comenzar polling
            await application.initialize()
            await application.start()
            
            # Iniciar polling con drop_pending_updates=True para evitar conflictos
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=2.0,  # Intervalo más largo entre peticiones
                timeout=30
            )
            
            # Mantener el bot corriendo
            # En threads secundarios, usamos un loop simple sin señales
            try:
                while not _shutdown_event.is_set():
                    await asyncio.sleep(1)
            except (asyncio.CancelledError, KeyboardInterrupt):
                print("\n⚠️ Bot interrumpido")
                pass
            
        except Conflict as e:
            print(f"\n❌ ERROR DE CONFLICTO: {e}")
            print("\n🔍 Hay otra instancia del bot corriendo.")
            print("📋 SOLUCIONES:")
            print("   1. Cierra todas las ventanas/terminales donde esté corriendo el bot")
            print("   2. Abre el Administrador de Tareas y cierra todos los procesos 'python.exe'")
            print("   3. Espera 10 segundos y vuelve a ejecutar")
            return
            
        except Exception as e:
            print(f"❌ Error al iniciar bot: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n🔄 Cerrando bot...")
            try:
                if _application:
                    if _application.updater.running:
                        await _application.updater.stop()
                    if _application.running:
                        await _application.stop()
                    await _application.shutdown()
                    print("✅ Bot cerrado correctamente")
            except Exception as e:
                print(f"⚠️ Error al cerrar: {e}")
    
    try:
        # Detectar si estamos en el thread principal o secundario
        is_main_thread = threading.current_thread() is threading.main_thread()
        
        if is_main_thread:
            print("ℹ️ Ejecutando en thread principal")
        else:
            print("ℹ️ Ejecutando en thread secundario (modo daemon)")
        
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        if threading.current_thread() is threading.main_thread():
            print("\n⚠️ Interrupción del usuario (Ctrl+C)")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if threading.current_thread() is threading.main_thread():
            print("👋 Bot finalizado")
