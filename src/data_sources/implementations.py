"""
Implementaciones concretas de fuentes de datos meteorológicos.

Este módulo agrupa todas las implementaciones de `BaseWeatherSource` para
mantener el código organizado y reducir la dispersión de archivos.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from .base_source import BaseWeatherSource

# Importaciones opcionales para AWS (Radar IDEAM)
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

logger = logging.getLogger(__name__)


# --- OpenMeteo ---
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


# --- OpenWeatherMap ---
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


# --- Meteosource ---
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


# --- MeteoBlue ---
class MeteoBlueSource(BaseWeatherSource):
    """
    Fuente de datos para MeteoBlue API.

    Esta clase implementa la interfaz `BaseWeatherSource` para consumir la API de MeteoBlue.
    
    Características específicas:
    - **Alta Precisión**: MeteoBlue es conocido por sus modelos de alta resolución.
    - **Formatos**: Soporta JSON y Protobuf (aunque aquí usamos JSON por simplicidad).
    - **Paquetes**: La API se divide en "paquetes" (basic-1h, basic-day) que deben solicitarse explícitamente.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://my.meteoblue.com/packages",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Inicializa la fuente MeteoBlue.

        Args:
            api_key: API key de MeteoBlue
            base_url: URL base de la API
            timeout: Timeout de peticiones HTTP
            max_retries: Número máximo de reintentos

        Raises:
            ValueError: Si no se proporciona API key
        """
        if not api_key:
            raise ValueError("MeteoBlue requiere una API key")

        super().__init__(
            name="MeteoBlue",
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

    def get_current_weather(
        self, latitude: float, longitude: float, format: str = "json", **kwargs
    ) -> Dict[str, Any]:
        """
        Obtiene el clima actual desde MeteoBlue.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            format: Formato de respuesta (json, protobuf)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del clima actual estandarizados
        """
        logger.info(
            f"Obteniendo clima actual de MeteoBlue para "
            f"({latitude}, {longitude})"
        )

        # MeteoBlue usa un formato específico de URL
        endpoint = f"basic-1h_package?lat={latitude}&lon={longitude}&apikey={self.api_key}&format={format}"

        try:
            response = self._make_request(endpoint, params={})
            data = response.json()

            # Estandarizar respuesta (estructura específica de MeteoBlue)
            data_1h = data.get("data_1h", {})
            if data_1h and len(data_1h) > 0:
                current = data_1h[-1]  # Último dato disponible
            else:
                current = {}

            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "temperature": current.get("temperature"),
                "humidity": current.get("relative_humidity"),
                "precipitation": current.get("precipitation"),
                "wind_speed": current.get("wind_speed"),
                "wind_direction": current.get("wind_direction"),
                "pressure": current.get("pressure_msl"),
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
        format: str = "json",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene el pronóstico del clima desde MeteoBlue.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días de pronóstico
            format: Formato de respuesta (json, protobuf)
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Datos del pronóstico estandarizados
        """
        logger.info(
            f"Obteniendo pronóstico de {days} días desde MeteoBlue "
            f"para ({latitude}, {longitude})"
        )

        # MeteoBlue tiene diferentes paquetes según los días
        if days <= 1:
            package = "basic-1h_package"
        elif days <= 5:
            package = "basic-day_package"
        else:
            package = "basic-16d_package"

        endpoint = f"{package}?lat={latitude}&lon={longitude}&apikey={self.api_key}&format={format}"

        try:
            response = self._make_request(endpoint, params={})
            data = response.json()

            # Estandarizar respuesta
            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "forecast_days": days,
                "data": data,
                "raw_data": data,
            }

            logger.debug(f"Pronóstico obtenido exitosamente")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener pronóstico: {e}")
            raise


# --- SIATA ---
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


# --- Radar IDEAM ---
class RadarIDEAMSource(BaseWeatherSource):
    """
    Fuente de datos para Radar IDEAM desde AWS S3.

    El IDEAM almacena datos de radar en formato binario en AWS S3.
    Esta implementación accede a esos datos y los procesa.
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        bucket_name: str = "ideam-radar",
        base_url: str = "https://s3.amazonaws.com/ideam-radar/",
        timeout: int = 60,  # Más tiempo para descargas grandes
        max_retries: int = 3,
    ):
        """
        Inicializa la fuente Radar IDEAM.

        Args:
            aws_access_key_id: AWS Access Key ID (opcional si hay credenciales)
            aws_secret_access_key: AWS Secret Access Key
            bucket_name: Nombre del bucket S3
            base_url: URL base del bucket
            timeout: Timeout de peticiones HTTP
            max_retries: Número máximo de reintentos
        """
        super().__init__(
            name="Radar IDEAM",
            base_url=base_url,
            api_key=None,
            timeout=timeout,
            max_retries=max_retries,
        )

        self.bucket_name = bucket_name
        self.s3_client = None

        # Configurar cliente S3 si hay credenciales
        if aws_access_key_id and aws_secret_access_key and AWS_AVAILABLE:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                )
                logger.info("Cliente S3 configurado con credenciales")
            except Exception as e:
                logger.warning(f"Error al configurar cliente S3: {e}")
        elif not AWS_AVAILABLE:
            logger.warning("boto3 no disponible. Instala boto3 para acceso S3.")

    def _list_radar_files(
        self, date: Optional[datetime] = None, limit: int = 10
    ) -> List[str]:
        """
        Lista los archivos de radar disponibles.

        Args:
            date: Fecha para buscar archivos (por defecto hoy)
            limit: Número máximo de archivos a retornar

        Returns:
            List[str]: Lista de nombres de archivos
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y%m%d")
        prefix = f"RAW{date_str}"

        try:
            if self.s3_client and AWS_AVAILABLE:
                # Usar boto3 para listar
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=prefix, MaxKeys=limit
                )
                files = [
                    obj["Key"]
                    for obj in response.get("Contents", [])
                    if obj["Key"].endswith(".RAW")
                ]
            else:
                # Intentar acceso público (puede no funcionar)
                logger.warning(
                    "No hay credenciales AWS o boto3 no disponible. "
                    "Intentando acceso público al bucket."
                )
                files = []

            logger.debug(f"Se encontraron {len(files)} archivos de radar")
            return files

        except Exception as e:
            if AWS_AVAILABLE:
                logger.error(f"Error al listar archivos de radar: {e}")
            else:
                logger.warning(f"boto3 no disponible: {e}")
            return []

    def get_current_weather(
        self, latitude: float, longitude: float, **kwargs
    ) -> Dict[str, Any]:
        """
        Obtiene datos de radar actuales desde IDEAM.

        Nota: Los datos de radar son imágenes, no datos puntuales.
        Este método retorna metadatos sobre el radar más reciente.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Metadatos del radar más reciente
        """
        logger.info(
            f"Obteniendo datos de radar IDEAM para "
            f"({latitude}, {longitude})"
        )

        try:
            # Obtener archivo de radar más reciente
            files = self._list_radar_files(limit=1)

            if not files:
                raise Exception("No hay archivos de radar disponibles")

            latest_file = files[0]

            # Extraer información del nombre del archivo
            # Formato típico: RAW20240115120000.RAW
            file_date_str = latest_file.replace("RAW", "").replace(".RAW", "")
            file_date = datetime.strptime(file_date_str, "%Y%m%d%H%M%S")

            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "radar_file": latest_file,
                "radar_timestamp": file_date.isoformat(),
                "file_url": f"{self.base_url}{latest_file}",
                "note": (
                    "Los datos de radar son imágenes binarias. "
                    "Se requiere procesamiento adicional para extraer "
                    "valores puntuales."
                ),
            }

            logger.debug(f"Datos de radar obtenidos exitosamente")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener datos de radar: {e}")
            raise

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Obtiene datos de radar históricos desde IDEAM.

        Args:
            latitude: Latitud de la ubicación
            longitude: Longitud de la ubicación
            days: Número de días hacia atrás
            **kwargs: Argumentos adicionales

        Returns:
            Dict[str, Any]: Lista de archivos de radar disponibles
        """
        logger.info(
            f"Obteniendo datos de radar históricos de {days} días "
            f"desde IDEAM para ({latitude}, {longitude})"
        )

        try:
            all_files = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                files = self._list_radar_files(date=date, limit=24)
                all_files.extend(files)

            standardized = {
                "source": self.name,
                "timestamp": datetime.now().isoformat(),
                "location": {"lat": latitude, "lon": longitude},
                "forecast_days": days,
                "radar_files": all_files,
                "count": len(all_files),
                "note": (
                    "Los datos de radar son imágenes binarias. "
                    "Se requiere procesamiento adicional."
                ),
            }

            logger.debug(f"Se encontraron {len(all_files)} archivos de radar")
            return standardized

        except Exception as e:
            logger.error(f"Error al obtener datos de radar históricos: {e}")
            raise
