"""
Aplicación para PRODUCCIÓN - Sistema de Reportes CNE
Usa Waitress para mejor rendimiento y estabilidad
"""
import threading
from flask import Flask
from waitress import serve
from config import SECRET_KEY
from routes import registrar_rutas
from telegram_bot import iniciar_bot_telegram

# Crear aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Configuración de producción
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['TESTING'] = False

# Registrar rutas
registrar_rutas(app)

if __name__ == '__main__':
    # Iniciar bot en hilo daemon
    bot_thread = threading.Thread(target=iniciar_bot_telegram, daemon=True)
    bot_thread.start()
    
    print("\n" + "="*70)
    print("🚀 SISTEMA DE REPORTES CNE - MODO PRODUCCIÓN")
    print("="*70)
    print("🌐 Web: http://0.0.0.0:5000")
    print("📱 Bot: Activo")
    print("⚡ Servidor: Waitress (optimizado para producción)")
    print("🔒 Debug: Desactivado")
    print("="*70 + "\n")
    
    # Iniciar Waitress (servidor de producción)
    # Configurado para manejar múltiples conexiones simultáneas
    serve(
        app,
        host='16.1.1.118',
        port=5555,
        threads=4,              # Número de threads para manejar requests
        channel_timeout=60,     # Timeout de conexión
        cleanup_interval=30,    # Limpieza de conexiones antiguas
        _quiet=False           # Mostrar logs
    )
