"""
Implementación de la fuente de datos Open-Meteo.

Open-Meteo es una API gratuita que no requiere API key y proporciona
datos meteorológicos históricos, actuales y de pronóstico.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from .base_source import BaseWeatherSource

logger = logging.getLogger(__name__)


class OpenMeteoSource(BaseWeatherSource):
    """
    Fuente de datos para Open-Meteo API.

    Esta API es gratuita y no requiere API key. Proporciona datos
    meteorológicos con resolución horaria y diaria.
    """

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Inicializa la fuente Open-Meteo.

        Args:
            base_url: URL base de la API
            timeout: Timeout de peticiones HTTP
            max_retries: Número máximo de reintentos
        """
        super().__init__(
            name="Open-Meteo",
            base_url=base_url,
            api_key=None,  # No requiere API key
            timeout=timeout,
            max_retries=max_retries,
        )

    def get_current_weather(
        self, latitude: float, longitude: float, timezone: str = "America/Bogota", **kwargs
    ) -> Dict[str, Any]:
        """
        Obtiene el clima actual desde Open-Meteo.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            timezone: Zona horaria (por defecto America/Bogota)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del clima actual estandarizados
        """
        logger.info(
            f"Obteniendo clima actual de Open-Meteo para "
            f"({latitude}, {longitude})"
        )

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "weather_code,wind_speed_10m,wind_direction_10m,"
                "surface_pressure"
            ),
            "timezone": timezone,
        }

        try:
            response = self._make_request("forecast", params=params)
            data = response.json()

            # Estandarizar respuesta
            current = data.get("current", {})
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation", 0),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "pressure": current.get("surface_pressure"),
                "weather_code": current.get("weather_code"),
                "raw_data": data,
            }

            logger.debug(f"Datos obtenidos exitosamente: {standardized}")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener clima actual: {e}")
            raise

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
        timezone: str = "America/Bogota",
        hourly: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene el pronóstico del clima desde Open-Meteo.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días de pronóstico (máximo 16)
            timezone: Zona horaria
            hourly: Si es True, datos horarios; si es False, datos diarios
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del pronóstico estandarizados
        """
        logger.info(
            f"Obteniendo pronóstico de {days} días desde Open-Meteo "
            f"para ({latitude}, {longitude})"
        )

        # Limitar días a 16 (máximo de Open-Meteo)
        days = min(days, 16)

        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": days,
        }

        if hourly:
            params["hourly"] = (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "weather_code,wind_speed_10m,wind_direction_10m"
            )
        else:
            params["daily"] = (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,weather_code,wind_speed_10m_max"
            )

        try:
            response = self._make_request("forecast", params=params)
            data = response.json()

            # Estandarizar respuesta
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "forecast_days": days,
                "hourly": hourly,
                "data": data.get("hourly" if hourly else "daily", {}),
                "raw_data": data,
            }

            logger.debug(f"Pronóstico obtenido exitosamente")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener pronóstico: {e}")
            raise


