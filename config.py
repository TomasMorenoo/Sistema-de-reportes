"""
Configuración general de la aplicación
"""
import os

# Configuración Flask
SECRET_KEY = 'tu-clave-secreta-cambiar-en-produccion'

# Configuración Telegram
TELEGRAM_TOKEN = '8568642871:AAEqnzxW1m4GW5las2cAGb9hQKgiQ05gvNw'

# Estados del ConversationHandler - CREAR
PISO, OFICINA, QUIEN, RAZON, ESTADO, RESUELTO_POR, FECHA_RESOLUCION = range(7)

# Estados del ConversationHandler - ACTUALIZAR
ACTUALIZAR_ID, ACTUALIZAR_ESTADO, ACTUALIZAR_RESUELTO_POR, ACTUALIZAR_FECHA = range(7, 11)

# Lista de empleados
EMPLEADOS = ['Tomas', 'Norela', 'Nahuel', 'Adrian', 'Marcelo', 'Chloe']

# Paths de base de datos
DB_PATH = (r'\\16.1.1.118\db\datosReportes.db')
DB_OFICINAS_PATH = r'\\16.1.1.118\db\OficinasCne.db'
