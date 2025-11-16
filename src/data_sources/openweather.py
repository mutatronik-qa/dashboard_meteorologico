"""
Implementación de la fuente de datos OpenWeatherMap.

OpenWeatherMap es una API popular que requiere API key y proporciona
datos meteorológicos actuales y pronósticos de hasta 5 días.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from .base_source import BaseWeatherSource

logger = logging.getLogger(__name__)


class OpenWeatherSource(BaseWeatherSource):
    """
    Fuente de datos para OpenWeatherMap API.

    Requiere API key que se puede obtener gratuitamente en
    https://openweathermap.org/api
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openweathermap.org/data/2.5",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Inicializa la fuente OpenWeatherMap.

        Args:
            api_key: API key de OpenWeatherMap
            base_url: URL base de la API
            timeout: Timeout de peticiones HTTP
            max_retries: Número máximo de reintentos

        Raises:
            ValueError: Si no se proporciona API key
        """
        if not api_key:
            raise ValueError("OpenWeatherMap requiere una API key")

        super().__init__(
            name="OpenWeatherMap",
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def get_current_weather(
        self, latitude: float, longitude: float, units: str = "metric", **kwargs
    ) -> Dict[str, Any]:
        """
        Obtiene el clima actual desde OpenWeatherMap.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            units: Unidades (metric, imperial, kelvin)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del clima actual estandarizados
        """
        logger.info(
            f"Obteniendo clima actual de OpenWeatherMap para "
            f"({latitude}, {longitude})"
        )

        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": units,
        }

        try:
            response = self._make_request("weather", params=params)
            data = response.json()

            # Estandarizar respuesta
            main = data.get("main", {})
            wind = data.get("wind", {})
            weather = data.get("weather", [{}])[0]

            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {
                    "lat": latitude,
                    "lon": longitude,
                    "name": data.get("name"),
                    "country": data.get("sys", {}).get("country"),
                },
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "humidity": main.get("humidity"),
                "pressure": main.get("pressure"),
                "wind_speed": wind.get("speed"),
                "wind_direction": wind.get("deg"),
                "visibility": data.get("visibility"),
                "clouds": data.get("clouds", {}).get("all"),
                "weather_code": weather.get("id"),
                "weather_description": weather.get("description"),
                "weather_main": weather.get("main"),
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
        units: str = "metric",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene el pronóstico del clima desde OpenWeatherMap.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días (máximo 5 para versión gratuita)
            units: Unidades (metric, imperial, kelvin)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del pronóstico estandarizados
        """
        logger.info(
            f"Obteniendo pronóstico de {days} días desde OpenWeatherMap "
            f"para ({latitude}, {longitude})"
        )

        # OpenWeatherMap free tier solo permite 5 días
        days = min(days, 5)

        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": units,
            "cnt": days * 8,  # 8 mediciones por día (cada 3 horas)
        }

        try:
            response = self._make_request("forecast", params=params)
            data = response.json()

            # Estandarizar respuesta
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {
                    "lat": latitude,
                    "lon": longitude,
                    "name": data.get("city", {}).get("name"),
                    "country": data.get("city", {}).get("country"),
                },
                "forecast_days": days,
                "forecasts": data.get("list", []),
                "raw_data": data,
            }

            logger.debug(f"Pronóstico obtenido exitosamente")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener pronóstico: {e}")
            raise


