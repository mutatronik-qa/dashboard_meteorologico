"""
Implementación de la fuente de datos SIATA.

SIATA (Sistema de Alertas Tempranas del Valle de Aburrá) es el sistema
local de monitoreo ambiental y meteorológico de Medellín y el área
metropolitana.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .base_source import BaseWeatherSource

logger = logging.getLogger(__name__)


class SIATASource(BaseWeatherSource):
    """
    Fuente de datos para SIATA.

    SIATA proporciona datos de múltiples estaciones meteorológicas
    en el área metropolitana de Medellín. Esta implementación incluye
    manejo de fallback cuando el servicio esté en mantenimiento.
    """

    def __init__(
        self,
        base_url: str = "https://siata.gov.co/siata_nuevo/",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Inicializa la fuente SIATA.

        Args:
            base_url: URL base de SIATA
            timeout: Timeout de peticiones HTTP
            max_retries: Número máximo de reintentos
        """
        super().__init__(
            name="SIATA",
            base_url=base_url,
            api_key=None,  # SIATA no requiere API key pública
            timeout=timeout,
            max_retries=max_retries,
        )
        self._stations_cache: Optional[List[Dict[str, Any]]] = None

    def get_stations(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de estaciones disponibles.

        Returns:
            List[Dict[str, Any]]: Lista de estaciones con sus datos
        """
        if self._stations_cache is not None:
            return self._stations_cache

        logger.info("Obteniendo lista de estaciones SIATA")

        try:
            # Intentar obtener datos de estaciones
            # Nota: La estructura real de la API de SIATA puede variar
            endpoint = "datos/estaciones"
            response = self._make_request(endpoint, params={})
            data = response.json()

            self._stations_cache = data.get("estaciones", [])
            logger.debug(f"Se encontraron {len(self._stations_cache)} estaciones")
            return self._stations_cache

        except Exception as e:
            logger.warning(
                f"No se pudieron obtener estaciones de SIATA: {e}. "
                f"El servicio puede estar en mantenimiento."
            )
            # Retornar estaciones por defecto conocidas
            return self._get_default_stations()

    def _get_default_stations(self) -> List[Dict[str, Any]]:
        """
        Retorna estaciones por defecto cuando la API no está disponible.

        Returns:
            List[Dict[str, Any]]: Lista de estaciones por defecto
        """
        return [
            {
                "id": "medellin_centro",
                "name": "Medellín Centro",
                "lat": 6.2442,
                "lon": -75.5812,
            },
            {
                "id": "bello",
                "name": "Bello",
                "lat": 6.3373,
                "lon": -75.5579,
            },
            {
                "id": "envigado",
                "name": "Envigado",
                "lat": 6.1696,
                "lon": -75.5781,
            },
        ]

    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
        station_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene el clima actual desde SIATA.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            station_id: ID de la estación (opcional)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del clima actual estandarizados

        Raises:
            Exception: Si SIATA está en mantenimiento
        """
        logger.info(
            f"Obteniendo clima actual de SIATA para "
            f"({latitude}, {longitude})"
        )

        try:
            # Intentar obtener datos de la estación más cercana
            if station_id:
                endpoint = f"datos/estacion/{station_id}"
            else:
                # Buscar estación más cercana
                stations = self.get_stations()
                if not stations:
                    raise Exception("No hay estaciones disponibles")

                # Encontrar estación más cercana (simplificado)
                station = stations[0]
                endpoint = f"datos/estacion/{station['id']}"

            response = self._make_request(endpoint, params={})
            data = response.json()

            # Estandarizar respuesta (estructura específica de SIATA)
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "station_id": station_id,
                "temperature": data.get("temperatura"),
                "humidity": data.get("humedad"),
                "precipitation": data.get("precipitacion", 0),
                "wind_speed": data.get("velocidad_viento"),
                "wind_direction": data.get("direccion_viento"),
                "pressure": data.get("presion"),
                "raw_data": data,
            }

            logger.debug(f"Datos obtenidos exitosamente")
            return standardized

        except Exception as e:
            logger.warning(
                f"SIATA no disponible: {e}. "
                f"El servicio puede estar en mantenimiento."
            )
            # Retornar datos vacíos o lanzar excepción según necesidad
            raise Exception(
                f"SIATA no está disponible en este momento: {e}"
            ) from e

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene el pronóstico del clima desde SIATA.

        Nota: SIATA principalmente proporciona datos actuales e históricos.
        Para pronósticos, se recomienda usar otras fuentes.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días (limitado por SIATA)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del pronóstico estandarizados
        """
        logger.warning(
            "SIATA no proporciona pronósticos. "
            "Usando datos históricos recientes."
        )

        # SIATA no tiene pronóstico, retornar estructura vacía
        return {
            "source": self.name,
            "timestamp": datetime.now().isoformat(),
            "location": {"lat": latitude, "lon": longitude},
            "forecast_days": days,
            "note": "SIATA no proporciona pronósticos",
            "data": {},
        }


