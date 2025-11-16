"""
Procesador de datos meteorológicos.

Este módulo proporciona funcionalidad para estandarizar, combinar y
procesar datos de múltiples fuentes meteorológicas.
"""

from typing import Dict, Any, List, Optional
import logging
import pandas as pd
from datetime import datetime
from .validators import detect_anomalies, validate_temperature, validate_humidity
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Procesador de datos meteorológicos.

    Esta clase estandariza datos de diferentes fuentes, convierte unidades,
    combina datos de múltiples ubicaciones y fuentes, y valida los datos.
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Inicializa el procesador de datos.

        Args:
            cache_manager: Gestor de caché opcional
        """
        self.cache_manager = cache_manager
        logger.info("DataProcessor inicializado")

    def standardize_data(
        self, data: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """
        Estandariza datos de diferentes fuentes a un formato común.

        Args:
            data: Datos en formato de la fuente original
            source: Nombre de la fuente de datos

        Returns:
            Dict[str, Any]: Datos estandarizados
        """
        logger.debug(f"Estandarizando datos de {source}")

        standardized = {
            "source": source,
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "location": data.get("location", {}),
        }

        # Mapear campos comunes
        field_mapping = {
            "temperature": ["temperature", "temp", "temperature_2m"],
            "humidity": ["humidity", "relative_humidity", "relative_humidity_2m"],
            "precipitation": ["precipitation", "precip", "precipitation_sum"],
            "wind_speed": ["wind_speed", "windspeed", "wind_speed_10m"],
            "wind_direction": [
                "wind_direction",
                "wind_deg",
                "wind_angle",
                "wind_direction_10m",
            ],
            "pressure": ["pressure", "surface_pressure", "pressure_msl"],
        }

        for standard_field, possible_fields in field_mapping.items():
            for field in possible_fields:
                if field in data and data[field] is not None:
                    standardized[standard_field] = data[field]
                    break

        # Convertir unidades si es necesario
        standardized = self._convert_units(standardized, source)

        # Validar datos
        anomalies = detect_anomalies(standardized)
        if anomalies:
            standardized["anomalies"] = anomalies
            logger.warning(
                f"Se detectaron {len(anomalies)} anomalías en datos de {source}"
            )

        return standardized

    def _convert_units(
        self, data: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """
        Convierte unidades a formato estándar.

        Unidades estándar:
        - Temperatura: Celsius
        - Humedad: Porcentaje (0-100)
        - Precipitación: mm
        - Velocidad del viento: km/h
        - Presión: hPa

        Args:
            data: Datos a convertir
            source: Fuente de datos (para determinar unidades originales)

        Returns:
            Dict[str, Any]: Datos con unidades convertidas
        """
        # OpenWeatherMap puede usar Kelvin
        if source == "OpenWeatherMap" and "temperature" in data:
            temp = data["temperature"]
            if temp and temp > 100:  # Probablemente en Kelvin
                data["temperature"] = temp - 273.15
                logger.debug("Temperatura convertida de Kelvin a Celsius")

        # Convertir velocidad del viento de m/s a km/h si es necesario
        if "wind_speed" in data and data["wind_speed"]:
            # OpenWeatherMap usa m/s, Open-Meteo usa km/h
            if source == "OpenWeatherMap":
                data["wind_speed"] = data["wind_speed"] * 3.6
                logger.debug("Velocidad del viento convertida de m/s a km/h")

        return data

    def combine_sources(
        self, data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combina datos de múltiples fuentes.

        Args:
            data_list: Lista de diccionarios con datos de diferentes fuentes

        Returns:
            Dict[str, Any]: Datos combinados con promedios y estadísticas
        """
        if not data_list:
            return {}

        logger.info(f"Combinando datos de {len(data_list)} fuentes")

        # Agrupar por campo
        combined = {
            "sources": [d.get("source") for d in data_list],
            "timestamp": datetime.now().isoformat(),
            "location": data_list[0].get("location", {}),
        }

        # Calcular promedios para campos numéricos
        numeric_fields = [
            "temperature",
            "humidity",
            "precipitation",
            "wind_speed",
            "pressure",
        ]

        for field in numeric_fields:
            values = [
                d.get(field)
                for d in data_list
                if d.get(field) is not None
            ]
            if values:
                combined[f"{field}_mean"] = sum(values) / len(values)
                combined[f"{field}_min"] = min(values)
                combined[f"{field}_max"] = max(values)
                combined[f"{field}_count"] = len(values)

        # Usar el valor más reciente o promedio para campos principales
        for field in numeric_fields:
            if f"{field}_mean" in combined:
                combined[field] = combined[f"{field}_mean"]

        return combined

    def aggregate_locations(
        self, data_list: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Agrega datos de múltiples ubicaciones en un DataFrame.

        Args:
            data_list: Lista de diccionarios con datos de diferentes ubicaciones

        Returns:
            pd.DataFrame: DataFrame con datos agregados
        """
        if not data_list:
            return pd.DataFrame()

        logger.info(f"Agregando datos de {len(data_list)} ubicaciones")

        # Convertir a DataFrame
        df = pd.DataFrame(data_list)

        # Establecer índice si hay timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)

        return df

    def to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convierte datos estandarizados a DataFrame.

        Args:
            data: Diccionario con datos estandarizados

        Returns:
            pd.DataFrame: DataFrame con los datos
        """
        # Si los datos tienen estructura de pronóstico con listas
        if "data" in data and isinstance(data["data"], dict):
            # Datos horarios o diarios de Open-Meteo
            df = pd.DataFrame(data["data"])
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"])
                df.set_index("time", inplace=True)
            return df

        # Datos simples de un punto en el tiempo
        flat_data = {
            "timestamp": pd.to_datetime(data.get("timestamp", datetime.now())),
            "source": data.get("source"),
            "temperature": data.get("temperature"),
            "humidity": data.get("humidity"),
            "precipitation": data.get("precipitation", 0),
            "wind_speed": data.get("wind_speed"),
            "wind_direction": data.get("wind_direction"),
            "pressure": data.get("pressure"),
        }

        df = pd.DataFrame([flat_data])
        df.set_index("timestamp", inplace=True)
        return df

    def validate_and_clean(
        self, data: Dict[str, Any], location: str = "Medellín"
    ) -> Dict[str, Any]:
        """
        Valida y limpia datos meteorológicos.

        Args:
            data: Datos a validar
            location: Nombre de la ubicación

        Returns:
            Dict[str, Any]: Datos validados y limpiados
        """
        # Detectar anomalías
        anomalies = detect_anomalies(data, location)

        # Filtrar errores críticos
        critical_errors = [
            a for a in anomalies if a.get("severity") == "error"
        ]

        if critical_errors:
            logger.error(
                f"Se encontraron {len(critical_errors)} errores críticos. "
                f"Datos pueden ser inválidos."
            )
            data["validation_errors"] = critical_errors

        # Limpiar valores None o inválidos
        cleaned = data.copy()
        for key, value in cleaned.items():
            if value is None or (isinstance(value, float) and pd.isna(value)):
                # Intentar usar valor por defecto razonable
                if key == "precipitation":
                    cleaned[key] = 0.0
                elif key in ["humidity", "wind_speed"]:
                    cleaned[key] = None  # Mantener None para campos críticos

        return cleaned


