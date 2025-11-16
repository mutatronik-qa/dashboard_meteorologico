"""
Implementación de la fuente de datos Meteosource.

Meteosource es una API comercial que proporciona datos meteorológicos
de alta calidad con diferentes niveles de suscripción.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from .base_source import BaseWeatherSource

logger = logging.getLogger(__name__)


class MeteosourceSource(BaseWeatherSource):
    """
    Fuente de datos para Meteosource API.

    Requiere API key que se puede obtener en
    https://www.meteosource.com/
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://www.meteosource.com/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Inicializa la fuente Meteosource.

        Args:
            api_key: API key de Meteosource
            base_url: URL base de la API
            timeout: Timeout de peticiones HTTP
            max_retries: Número máximo de reintentos

        Raises:
            ValueError: Si no se proporciona API key
        """
        if not api_key:
            raise ValueError("Meteosource requiere una API key")

        super().__init__(
            name="Meteosource",
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def get_current_weather(
        self, latitude: float, longitude: float, sections: str = "current", **kwargs
    ) -> Dict[str, Any]:
        """
        Obtiene el clima actual desde Meteosource.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            sections: Secciones de datos a obtener (current, minutely, etc.)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del clima actual estandarizados
        """
        logger.info(
            f"Obteniendo clima actual de Meteosource para "
            f"({latitude}, {longitude})"
        )

        params = {
            "lat": latitude,
            "lon": longitude,
            "key": self.api_key,
            "sections": sections,
            "units": "metric",
        }

        try:
            response = self._make_request("free/point", params=params)
            data = response.json()

            # Estandarizar respuesta
            current = data.get("current", {})
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "temperature": current.get("temperature"),
                "humidity": current.get("humidity"),
                "precipitation": current.get("precipitation", {}).get("total", 0),
                "wind_speed": current.get("wind", {}).get("speed"),
                "wind_direction": current.get("wind", {}).get("angle"),
                "pressure": current.get("pressure"),
                "cloud_cover": current.get("cloud_cover"),
                "weather": current.get("weather"),
                "raw_data": data,
            }

            logger.debug(f"Datos obtenidos exitosamente")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener clima actual: {e}")
            raise

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
        sections: str = "daily",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene el pronóstico del clima desde Meteosource.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días de pronóstico
            sections: Secciones de datos (daily, hourly, etc.)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del pronóstico estandarizados
        """
        logger.info(
            f"Obteniendo pronóstico de {days} días desde Meteosource "
            f"para ({latitude}, {longitude})"
        )

        params = {
            "lat": latitude,
            "lon": longitude,
            "key": self.api_key,
            "sections": sections,
            "units": "metric",
            "tz": "America/Bogota",
        }

        try:
            response = self._make_request("free/point", params=params)
            data = response.json()

            # Estandarizar respuesta
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "forecast_days": days,
                "data": data.get(sections, {}),
                "raw_data": data,
            }

            logger.debug(f"Pronóstico obtenido exitosamente")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener pronóstico: {e}")
            raise


