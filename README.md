# 🌤️ Dashboard Meteorológico

Dashboard completo y profesional para visualización de datos meteorológicos con soporte para múltiples fuentes de datos, procesamiento avanzado y visualizaciones interactivas.

## 📋 Características

- **Múltiples Fuentes de Datos**: Soporte para Open-Meteo, OpenWeatherMap, Meteosource, MeteoBlue, SIATA y Radar IDEAM
- **Procesamiento Robusto**: Validación de datos, detección de anomalías y estandarización
- **Sistema de Caché**: Caché inteligente para evitar exceder límites de API
- **Visualizaciones Interactivas**: Gráficos con Plotly, mapas con Folium
- **Arquitectura Modular**: Código limpio, extensible y fácil de mantener
- **Tests Unitarios**: Suite completa de tests
- **Documentación Completa**: Docstrings y ejemplos

## 🗂️ Estructura del Proyecto

```
dashboard_meteorologico/
├── src/
│   ├── data_sources/      # Fuentes de datos meteorológicos
│   ├── processors/         # Procesamiento y validación
│   └── visualizers/        # Visualizaciones
├── config/                 # Configuración
├── notebooks/              # Jupyter notebooks de ejemplo
├── tests/                  # Tests unitarios
├── data/                   # Datos (raw, processed, cache)
└── main.py                 # Script principal CLI
```

## 🚀 Instalación

### Requisitos

- Python 3.8 o superior
- pip

### Pasos

1. **Clonar o descargar el proyecto**

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env y agregar tus API keys
   ```

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```env
# API Keys (opcionales, según las fuentes que quieras usar)
OPENWEATHER_API_KEY=tu_api_key_aqui
METEOSOURCE_API_KEY=tu_api_key_aqui
METEOBLUE_API_KEY=tu_api_key_aqui

# AWS (para Radar IDEAM)
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key

# Configuración
LOG_LEVEL=INFO
DEBUG_MODE=False
CACHE_TTL_MINUTES=15
```

### Ubicaciones

Edita `config/locations.json` para agregar o modificar ubicaciones del área metropolitana.

## 📖 Uso

### Línea de Comandos

```bash
# Obtener datos actuales para Medellín
python main.py --location Medellín

# Obtener pronóstico de 5 días
python main.py --location Medellín --forecast 5

# Usar una fuente específica
python main.py --location Medellín --source Open-Meteo

# Listar ubicaciones disponibles
python main.py --list-locations

# Listar fuentes de datos disponibles
python main.py --list-sources
```

### Python

```python
from src.data_sources import OpenMeteoSource
from src.visualizers.dashboard import Dashboard
from config import load_locations

# Crear fuente de datos
source = OpenMeteoSource()

# Obtener datos
locations = load_locations()
medellin = locations[0]
data = source.get_current_weather(medellin.lat, medellin.lon)

print(f"Temperatura: {data['temperature']}°C")
print(f"Humedad: {data['humidity']}%")

# Usar dashboard completo
dashboard = Dashboard([source])
result = dashboard.update({
    'lat': medellin.lat,
    'lon': medellin.lon,
    'name': medellin.name
})
```

### Jupyter Notebooks

Los notebooks en `notebooks/` proporcionan ejemplos detallados:

- `01_exploracion_apis.ipynb`: Explorar diferentes APIs
- `02_prueba_fetchers.ipynb`: Probar fetchers de datos
- `03_visualizacion.ipynb`: Crear visualizaciones
- `04_dashboard_completo.ipynb`: Dashboard completo

## 🔧 Fuentes de Datos

### Open-Meteo (Gratuita, sin API key)
- Datos actuales y pronósticos
- Datos históricos
- Resolución horaria y diaria

### OpenWeatherMap (Requiere API key)
- Datos actuales
- Pronóstico de 5 días
- API key gratuita disponible

### Meteosource (Requiere API key)
- Datos de alta calidad
- Múltiples niveles de suscripción

### MeteoBlue (Requiere API key)
- API profesional
- Datos de alta precisión

### SIATA (Local Medellín)
- Datos locales del área metropolitana
- Múltiples estaciones

### Radar IDEAM (Requiere credenciales AWS)
- Datos de radar meteorológico
- Acceso a archivos RAW desde S3

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/test_data_sources.py
```

## 📊 Visualizaciones

El proyecto incluye funciones para crear:

- **Mapas de temperatura** con Folium
- **Gráficos de comparación** entre ubicaciones
- **Series temporales** de variables meteorológicas
- **Gráficos de humedad** (barras, líneas, pie)
- **Rosas de viento** (gráficos polares)
- **Tarjetas de métricas** (KPIs)

## 🔮 Extensión

El proyecto está diseñado para ser fácilmente extensible:

1. **Agregar nueva fuente de datos**: Crear clase que herede de `BaseWeatherSource`
2. **Nuevos procesadores**: Extender `DataProcessor`
3. **Nuevas visualizaciones**: Agregar funciones en `plots.py`

## 📝 Código

- **Type hints** en todas las funciones
- **Docstrings** estilo Google
- **Manejo robusto de errores**
- **Logging comprehensivo**
- **PEP 8** compliant
- **Patrones de diseño**: Strategy, Factory

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- Open-Meteo por la API gratuita
- Todas las fuentes de datos meteorológicos utilizadas
- La comunidad de Python

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Desarrollado con ❤️ para el área metropolitana de Medellín**


