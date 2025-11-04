# 📋 Sistema de Gestión de Reportes

Sistema web para gestionar reportes de soporte técnico en oficinas, desarrollado con Flask y SQLite.

## 🚀 Características

- ✅ **CRUD Completo**: Crear, leer, actualizar y eliminar reportes
- 🏢 **Gestión de Oficinas**: Oficinas organizadas por pisos en base de datos remota
- 📊 **Estadísticas Visuales**: Dashboards con métricas de reportes
- 📥 **Exportación a Excel**: Genera archivos .xlsx con todos los reportes
- 👥 **Múltiples Resolvedores**: Asigna uno o varios responsables por reporte
- 🎨 **Interfaz Moderna**: Bootstrap 5 con iconos Font Awesome
- 🔍 **Selects Mejorados**: Select2 para búsqueda inteligente

## 📁 Estructura del Proyecto

```
proyecto/
├── app.py                   # Aplicación Flask principal
├── init_db.py               # Script de inicialización de BD
├── oficinas.py              # Gestor de oficinas (opcional)
├── datosReportes.db         # Base de datos local (se crea automáticamente)
├── templates/
│   ├── index.html           # Página principal - Lista de reportes
│   ├── nuevo.html           # Formulario nuevo reporte
│   ├── actualizar.html      # Actualizar estado de reportes
│   └── estadisticas.html    # Dashboard de estadísticas
└── static/
    └── images/
        └── soporte.ico      # Favicon
```

## 🗄️ Bases de Datos

### Local: `datosReportes.db`
Almacena los reportes con la siguiente estructura:

| Campo        | Tipo    | Descripción                |
|--------------|---------|----------------------------|
| id           | INTEGER | ID único (auto-incremental)|
| piso         | INTEGER | Número de piso (-3 a 4)    |
| oficina      | TEXT    | Nombre de la oficina       |
| quien        | TEXT    | Persona que reporta        |
| razon        | TEXT    | Descripción del problema   |
| estado       | TEXT    | pendiente/en proceso/resuelto |
| fecha        | TEXT    | Fecha de creación (dd/mm/yy) |
| resuelto_por | TEXT    | Persona(s) que resolvieron |

### Remota: `\\16.1.1.118\db\OficinasCne.db`
Almacena las oficinas disponibles:

| Campo  | Tipo    | Descripción           |
|--------|---------|----------------------|
| id     | INTEGER | ID único             |
| nombre | TEXT    | Nombre de oficina    |
| piso   | INTEGER | Piso donde se ubica  |

## ⚙️ Requisitos

```bash
pip install flask
pip install openpyxl
```

## 🔧 Instalación y Configuración

### 1. Clonar o descargar el proyecto

```bash
cd /ruta/al/proyecto
```

### 2. Verificar conexión a red compartida

Asegúrate de tener acceso a la ruta de red:
```
\\16.1.1.118\db\
```

### 3. Inicializar las bases de datos

```bash
python init_db.py
```

Este script:
- ✅ Crea la base de datos local `datosReportes.db`
- ✅ Verifica la conexión a la BD remota de oficinas
- ✅ Opcionalmente carga oficinas de ejemplo

**Salida esperada:**
```
🚀 Inicializando sistema de reportes...
==================================================
✅ Base de datos local inicializada correctamente
📁 Ubicación: C:\ruta\datosReportes.db

==================================================
Verificando base de datos de oficinas...
✅ Conexión exitosa a BD de oficinas remota
📍 \\16.1.1.118\db\OficinasCne.db
📊 X oficinas encontradas
```

### 4. (Opcional) Gestionar Oficinas

Si necesitas agregar/eliminar oficinas:

```bash
python oficinas.py
```

Menú interactivo con opciones:
1. 📋 Listar todas las oficinas
2. ➕ Agregar nueva oficina
3. ➕ Agregar múltiples oficinas
4. 🗑️ Eliminar oficina
5. 🚪 Salir

### 5. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en:
```
http://localhost:5555
```

O desde otra computadora en la red:
```
http://[IP-DEL-SERVIDOR]:5555
```

## 📱 Uso de la Aplicación

### Página Principal
- Ver todos los reportes ordenados por más recientes
- Filtrar visualmente por estado (badges de colores)
- Eliminar reportes con confirmación

### Crear Nuevo Reporte
1. Seleccionar **piso**
2. Las oficinas se filtran automáticamente según el piso
3. Completar: quién reporta, razón del problema, estado
4. Si el estado es "Resuelto":
   - Aparece selector de personas
   - Puedes agregar múltiples personas con el botón **+**
   - Puedes quitar personas con el botón **-**

### Actualizar Estado
- Lista solo reportes **pendientes** o **en proceso**
- Click en "Marcar como Resuelto" abre un modal
- Selecciona una o varias personas que resolvieron
- Confirma y el estado cambia automáticamente

### Estadísticas
Dashboard con métricas:
- 📊 Total de reportes
- 📈 Distribución por estado
- 🏢 Top 5 oficinas con más reportes
- 🏗️ Reportes por piso
- 👤 Top 5 personas que más resolvieron

### Exportar a Excel
- Descarga archivo `.xlsx` con todos los reportes
- Nombre de archivo incluye timestamp
- Columnas auto-ajustadas

## 🔍 Endpoints de Debug

### `/debugdb`
Muestra información de las bases de datos:
- Ruta de BD local
- Ruta de BD remota
- Cantidad de oficinas disponibles
- Estado de conexión

Acceso:
```
http://localhost:5555/debugdb
```

## 🎨 Características de la Interfaz

### Colores de Estados
- 🔴 **Rojo** (Pendiente): Reporte nuevo sin atender
- 🟡 **Amarillo** (En Proceso): Reporte en resolución
- 🟢 **Verde** (Resuelto): Reporte completado

### Navegación
- **Navbar** con accesos rápidos a todas las secciones
- **Botones con iconos** para mejor UX
- **Confirmaciones** antes de eliminar
- **Mensajes flash** para feedback inmediato

### Responsive Design
- Adaptable a móviles y tablets
- Tablas con scroll horizontal en pantallas pequeñas

## 🛠️ Solución de Problemas

### Error: No se puede conectar a BD de oficinas

**Síntomas:**
```
❌ Error al conectar con BD de oficinas remota
```

**Solución:**
1. Verificar que la ruta `\\16.1.1.118\db\` sea accesible
2. Comprobar permisos de red
3. Verificar que el archivo `OficinasCne.db` existe
4. Intentar acceder manualmente a la carpeta desde el explorador

### Error: Base de datos bloqueada

**Síntomas:**
```
sqlite3.OperationalError: database is locked
```

**Solución:**
1. Cerrar todas las conexiones a la BD
2. Reiniciar la aplicación Flask
3. Verificar que no haya otros procesos usando la BD

### Las oficinas no se cargan en el formulario

**Solución:**
1. Ejecutar `/debugdb` para verificar conexión
2. Revisar que haya oficinas cargadas:
   ```bash
   python oficinas.py
   # Opción 1 para listar
   ```
3. Verificar logs en consola de Flask

## 🔐 Seguridad

### Recomendaciones para Producción

1. **Cambiar SECRET_KEY** en `app.py`:
   ```python
   app.config['SECRET_KEY'] = 'tu-clave-super-secreta-y-aleatoria'
   ```

2. **Desactivar modo debug**:
   ```python
   app.run(host='0.0.0.0', port=5555, debug=False)
   ```

3. **Usar un servidor WSGI** (Gunicorn, uWSGI):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5555 app:app
   ```

## 📝 Notas Adicionales

- La BD local se crea automáticamente en el mismo directorio que `app.py`
- Las fechas se guardan en formato `dd/mm/yy`
- Los archivos Excel se generan con timestamp único
- La aplicación funciona en red local, accesible desde cualquier PC

## 🤝 Soporte

Para problemas o sugerencias, contacta al equipo de IT.

---

**Versión:** 2.0  
**Última actualización:** 2025  
**Tecnologías:** Flask, SQLite, Bootstrap 5, Select2, jQuery