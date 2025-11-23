"""
API REST para el sistema IoT.

Esta API expone endpoints para obtener datos meteorológicos actuales y pronósticos,
diseñada para ser consumida por dispositivos IoT y otros servicios.
"""

from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from config import get_settings
from src.processors.data_processor import DataProcessor
from src.processors.cache_manager import CacheManager
from src.data_sources import (
    OpenMeteoSource,
    OpenWeatherSource,
    MeteosourceSource,
    MeteoBlueSource,
    SIATASource,
    RadarIDEAMSource,
)

# Configuración
settings = get_settings()

app = FastAPI(
    title="Dashboard Meteorológico IoT API",
    description="API para consumo de datos meteorológicos por dispositivos IoT",
    version="1.0.0",
)

# Inicialización de componentes
cache_manager = CacheManager(
    cache_dir=settings.cache_dir, ttl_minutes=settings.cache_ttl_minutes
)
processor = DataProcessor(cache_manager=cache_manager)


def get_sources() -> list:
    """Helper para inicializar fuentes disponibles."""
    sources = []
    # Open-Meteo siempre disponible
    sources.append(OpenMeteoSource())
    
    if settings.openweather_api_key:
        sources.append(OpenWeatherSource(api_key=settings.openweather_api_key))
        
    # Se pueden agregar más fuentes aquí según disponibilidad de keys
    return sources


@app.get("/health")
async def health_check():
    """Endpoint de verificación de estado."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/weather/current/{location_name}")
async def get_current_weather(
    location_name: str,
    lat: float = Query(..., description="Latitud de la ubicación"),
    lon: float = Query(..., description="Longitud de la ubicación"),
):
    """
    Obtiene el clima actual para una ubicación específica.
    Combina datos de múltiples fuentes disponibles.
    """
    sources = get_sources()
    if not sources:
        raise HTTPException(status_code=503, detail="No hay fuentes de datos disponibles")

    data_list = []
    errors = []

    for source in sources:
        try:
            # Intentar obtener datos (usando caché si está disponible en el source/processor)
            # Nota: El caching real está en DataProcessor o implementado en cada source si se refactoriza.
            # Por ahora, llamamos directo.
            data = source.get_current_weather(lat, lon)
            
            # Estandarizar
            std_data = processor.standardize_data(data, source.name)
            data_list.append(std_data)
        except Exception as e:
            errors.append(f"{source.name}: {str(e)}")

    if not data_list:
        raise HTTPException(
            status_code=502, 
            detail=f"Fallo al obtener datos de todas las fuentes. Errores: {errors}"
        )

    # Combinar y validar
    combined = processor.combine_sources(data_list)
    cleaned = processor.validate_and_clean(combined, location_name)

    return cleaned


@app.get("/weather/forecast/{location_name}")
async def get_forecast(
    location_name: str,
    lat: float = Query(..., description="Latitud de la ubicación"),
    lon: float = Query(..., description="Longitud de la ubicación"),
    days: int = Query(5, ge=1, le=7, description="Días de pronóstico"),
):
    """
    Obtiene el pronóstico del clima.
    Por simplicidad, usa Open-Meteo como fuente principal para pronósticos.
    """
    # Usar Open-Meteo por defecto para pronósticos
    source = OpenMeteoSource()
    
    try:
        data = source.get_forecast(lat, lon, days=days)
        # Estandarizar (aunque get_forecast ya devuelve estructura, standardize puede pulir)
        # En este caso devolvemos la estructura estandarizada del source
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error obteniendo pronóstico: {str(e)}")
