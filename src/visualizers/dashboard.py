"""
Dashboard principal para visualización de datos meteorológicos.

Este módulo orquesta la obtención de datos, procesamiento y visualización,
soportando tanto modo Jupyter (ipywidgets) como modo Streamlit.
"""

from typing import Dict, Any, List, Optional
import logging
import pandas as pd
from datetime import datetime

from ..data_sources.base_source import BaseWeatherSource
from ..processors.data_processor import DataProcessor
from ..processors.cache_manager import CacheManager
from .plots import (
    create_temperature_map,
    create_comparison_chart,
    create_time_series,
    create_humidity_chart,
    create_wind_chart,
    create_metrics,
)
from .components import create_location_selector

logger = logging.getLogger(__name__)


class Dashboard:
    """
    Dashboard principal para datos meteorológicos.

    Esta clase orquesta la obtención de datos de múltiples fuentes,
    procesamiento, y generación de visualizaciones.
    """

    def __init__(
        self,
        sources: List[BaseWeatherSource],
        processor: Optional[DataProcessor] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Inicializa el dashboard.

        Args:
            sources: Lista de fuentes de datos disponibles
            processor: Procesador de datos (se crea uno si es None)
            cache_manager: Gestor de caché (se crea uno si es None)
        """
        self.sources = sources
        self.processor = processor or DataProcessor(cache_manager)
        self.cache_manager = cache_manager or CacheManager()

        logger.info(f"Dashboard inicializado con {len(sources)} fuentes")

    def get_data_for_location(
        self,
        latitude: float,
        longitude: float,
        source_names: Optional[List[str]] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos de todas las fuentes para una ubicación.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            source_names: Nombres de fuentes a usar (None = todas)
            use_cache: Si usar caché

        Returns:
            List[Dict[str, Any]]: Lista de datos estandarizados
        """
        logger.info(
            f"Obteniendo datos para ubicación ({latitude}, {longitude})"
        )

        results = []

        # Filtrar fuentes si se especifica
        sources_to_use = self.sources
        if source_names:
            sources_to_use = [
                s for s in self.sources if s.name in source_names
            ]

        for source in sources_to_use:
            try:
                # Verificar caché
                cache_key = {
                    "source": source.name,
                    "lat": latitude,
                    "lon": longitude,
                    "type": "current",
                }

                if use_cache:
                    cached_data = self.cache_manager.get(
                        source.name, cache_key
                    )
                    if cached_data:
                        logger.debug(f"Datos obtenidos del caché: {source.name}")
                        results.append(cached_data)
                        continue

                # Obtener datos de la fuente
                raw_data = source.get_current_weather(latitude, longitude)

                # Estandarizar datos
                standardized = self.processor.standardize_data(
                    raw_data, source.name
                )

                # Guardar en caché
                if use_cache:
                    self.cache_manager.set(source.name, cache_key, standardized)

                results.append(standardized)

            except Exception as e:
                logger.error(
                    f"Error al obtener datos de {source.name}: {e}"
                )
                continue

        logger.info(f"Se obtuvieron datos de {len(results)} fuentes")
        return results

    def get_forecast_for_location(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
        source_name: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Obtiene pronóstico para una ubicación.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días de pronóstico
            source_name: Nombre de la fuente (None = primera disponible)
            use_cache: Si usar caché

        Returns:
            Dict[str, Any]: Datos del pronóstico
        """
        logger.info(
            f"Obteniendo pronóstico de {days} días para "
            f"({latitude}, {longitude})"
        )

        # Seleccionar fuente
        source = None
        if source_name:
            source = next(
                (s for s in self.sources if s.name == source_name), None
            )
        else:
            # Usar primera fuente disponible
            source = self.sources[0] if self.sources else None

        if not source:
            raise ValueError("No hay fuentes de datos disponibles")

        try:
            # Verificar caché
            cache_key = {
                "source": source.name,
                "lat": latitude,
                "lon": longitude,
                "type": "forecast",
                "days": days,
            }

            if use_cache:
                cached_data = self.cache_manager.get(source.name, cache_key)
                if cached_data:
                    logger.debug("Pronóstico obtenido del caché")
                    return cached_data

            # Obtener pronóstico
            raw_data = source.get_forecast(latitude, longitude, days=days)

            # Estandarizar
            standardized = self.processor.standardize_data(
                raw_data, source.name
            )

            # Guardar en caché
            if use_cache:
                self.cache_manager.set(source.name, cache_key, standardized)

            return standardized

        except Exception as e:
            logger.error(f"Error al obtener pronóstico: {e}")
            raise

    def create_visualizations(
        self, data: List[Dict[str, Any]], location_name: str = "Ubicación"
    ) -> Dict[str, Any]:
        """
        Crea todas las visualizaciones para los datos.

        Args:
            data: Lista de datos estandarizados
            location_name: Nombre de la ubicación

        Returns:
            Dict[str, Any]: Diccionario con todas las visualizaciones
        """
        logger.info(f"Creando visualizaciones para {location_name}")

        visualizations = {}

        # Métricas principales
        if data:
            combined_data = self.processor.combine_sources(data)
            visualizations["metrics"] = create_metrics(combined_data)

        # Gráfico de comparación de temperatura
        visualizations["temperature_comparison"] = create_comparison_chart(
            data, metric="temperature"
        )

        # Gráfico de humedad
        visualizations["humidity_chart"] = create_humidity_chart(data)

        # Gráfico de viento
        visualizations["wind_chart"] = create_wind_chart(data)

        # Mapa de temperatura
        visualizations["temperature_map"] = create_temperature_map(data)

        return visualizations

    def update(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza el dashboard con datos de una ubicación.

        Args:
            location: Diccionario con lat, lon, name de la ubicación

        Returns:
            Dict[str, Any]: Datos y visualizaciones actualizadas
        """
        lat = location.get("lat")
        lon = location.get("lon")
        name = location.get("name", "Ubicación")

        # Obtener datos
        data = self.get_data_for_location(lat, lon)

        # Crear visualizaciones
        visualizations = self.create_visualizations(data, name)

        return {
            "location": location,
            "data": data,
            "visualizations": visualizations,
            "timestamp": datetime.now().isoformat(),
        }

    def get_available_sources(self) -> List[str]:
        """
        Obtiene lista de fuentes disponibles.

        Returns:
            List[str]: Nombres de fuentes disponibles
        """
        return [source.name for source in self.sources]


