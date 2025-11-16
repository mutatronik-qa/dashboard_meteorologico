"""
Implementación de la fuente de datos Radar IDEAM.

El IDEAM (Instituto de Hidrología, Meteorología y Estudios Ambientales)
proporciona datos de radar meteorológico desde AWS S3. Los datos están
en formato binario RAWXXXX.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from .base_source import BaseWeatherSource

logger = logging.getLogger(__name__)

# Importaciones opcionales para AWS
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("boto3 no está instalado. Funcionalidad AWS limitada.")


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

