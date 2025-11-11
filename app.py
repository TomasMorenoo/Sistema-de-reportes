"""
Aplicación principal - Sistema de Reportes CNE
"""
import threading
from flask import Flask
from config import SECRET_KEY
from routes import registrar_rutas
from telegram_bot import iniciar_bot_telegram

# Crear aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Registrar rutas
registrar_rutas(app)

if __name__ == '__main__':
    # Iniciar bot en hilo daemon
    bot_thread = threading.Thread(target=iniciar_bot_telegram, daemon=True)
    bot_thread.start()
    
    print("\n" + "="*60)
    print("🚀 SISTEMA DE REPORTES CNE")
    print("="*60)
    print("🌐 Web: http://16.1.1.118:5555")
    print("📱 Bot: Activo")
    print("="*60 + "\n")
    
    # Iniciar Flask
    app.run(host='16.1.1.118', port=5555, threaded=True)
