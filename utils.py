"""
Funciones de utilidad
"""

def normalizar_nombre(nombre):
    """
    Normaliza nombres para contar correctamente
    'Tomas', 'tomas' -> 'Tomas'
    """
    if not nombre:
        return ''
    nombre = nombre.lower().strip()
    return nombre.capitalize()

def dividir_nombres(nombre_completo):
    """
    Divide nombres cuando hay múltiples personas
    'Tomas, Nahuel, Chloe' -> ['Tomas', 'Nahuel', 'Chloe']
    Cada persona recibe crédito por el trabajo
    """
    if not nombre_completo:
        return []
    
    # Separar por comas
    nombres = [n.strip() for n in nombre_completo.split(',')]
    # Normalizar cada nombre
    return [normalizar_nombre(n) for n in nombres if n.strip()]
