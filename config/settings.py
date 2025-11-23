"""
Configuración central del proyecto usando Pydantic.

Este módulo define todas las configuraciones del sistema incluyendo
URLs de APIs, coordenadas de ubicaciones, parámetros de caché,
y variables de entorno para API keys.
"""

from typing import Dict, List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class LocationConfig(BaseSettings):
    """Configuración de una ubicación geográfica."""

    name: str = Field(..., description="Nombre de la ubicación")
    lat: float = Field(..., ge=-90, le=90, description="Latitud")
    lon: float = Field(..., ge=-180, le=180, description="Longitud")
    altitude: Optional[float] = Field(
        None, description="Altitud en metros sobre el nivel del mar"
    )

    class Config:
        """Configuración de Pydantic."""

        extra = "forbid"


class Settings(BaseSettings):
    """Configuración principal del proyecto."""

    # API Keys
    openweather_api_key: Optional[str] = Field(
        None, env="OPENWEATHER_API_KEY", description="API key de OpenWeatherMap"
    )
    meteosource_api_key: Optional[str] = Field(
        None, env="METEOSOURCE_API_KEY", description="API key de Meteosource"
    )
    meteoblue_api_key: Optional[str] = Field(
        None, env="METEOBLUE_API_KEY", description="API key de MeteoBlue"
    )
    aws_access_key_id: Optional[str] = Field(
        None, env="AWS_ACCESS_KEY_ID", description="AWS Access Key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        None, env="AWS_SECRET_ACCESS_KEY", description="AWS Secret Access Key"
    )

    # URLs de APIs
    openweather_base_url: str = Field(
        "https://api.openweathermap.org/data/2.5",
        description="URL base de OpenWeatherMap API",
    )
    openmeteo_base_url: str = Field(
        "https://api.open-meteo.com/v1",
        description="URL base de Open-Meteo API",
    )
    meteosource_base_url: str = Field(
        "https://www.meteosource.com/api/v1",
        description="URL base de Meteosource API",
    )
    meteoblue_base_url: str = Field(
        "https://my.meteoblue.com/packages",
        description="URL base de MeteoBlue API",
    )
    siata_base_url: str = Field(
        "https://siata.gov.co/siata_nuevo/",
        description="URL base de SIATA",
    )
    ideam_radar_url: str = Field(
        "https://s3.amazonaws.com/ideam-radar/",
        description="URL base del radar IDEAM en AWS S3",
    )

    # Configuración de ubicaciones
    default_location: str = Field(
        "Medellín", description="Ubicación por defecto"
    )
    timezone: str = Field(
        "America/Bogota", description="Zona horaria por defecto"
    )

    # Parámetros de caché
    cache_ttl_minutes: int = Field(
        15, ge=1, le=1440, description="TTL del caché en minutos"
    )
    cache_max_size: int = Field(
        1000, ge=1, description="Tamaño máximo del caché en MB"
    )

    # Parámetros de reintentos
    max_retries: int = Field(
        3, ge=0, le=10, description="Número máximo de reintentos"
    )
    retry_backoff_factor: float = Field(
        2.0, ge=1.0, description="Factor de backoff exponencial"
    )
    request_timeout: int = Field(
        30, ge=1, description="Timeout de peticiones HTTP en segundos"
    )

    # Configuración de logging
    log_level: str = Field(
        "INFO", description="Nivel de logging"
    )
    debug_mode: bool = Field(
        False, description="Modo debug activado"
    )
    log_file: str = Field(
        "logs/dashboard_meteorologico.log",
        description="Archivo de log",
    )

    # Rutas de datos
    data_dir: Path = Field(
        Path("data"), description="Directorio de datos"
    )
    raw_data_dir: Path = Field(
        Path("data/raw"), description="Directorio de datos sin procesar"
    )
    processed_data_dir: Path = Field(
        Path("data/processed"), description="Directorio de datos procesados"
    )
    cache_dir: Path = Field(
        Path("data/cache"), description="Directorio de caché"
    )

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Valida que el nivel de log sea válido."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"log_level debe ser uno de: {', '.join(valid_levels)}"
            )
        return v.upper()

    @validator("data_dir", "raw_data_dir", "processed_data_dir", "cache_dir")
    def create_directories(cls, v: Path) -> Path:
        """Crea los directorios si no existen."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        """Configuración de Pydantic."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Instancia global de configuración
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Obtiene la instancia global de configuración.

    Returns:
        Settings: Instancia de configuración
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def load_locations(filepath: Optional[str] = None) -> List[LocationConfig]:
    """
    Carga las ubicaciones desde un archivo JSON.

    Args:
        filepath: Ruta al archivo JSON. Si es None, usa locations.json
            en el directorio config.

    Returns:
        List[LocationConfig]: Lista de configuraciones de ubicaciones
    """
    import json

    if filepath is None:
        filepath = Path(__file__).parent / "locations.json"

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [LocationConfig(**location) for location in data.get("locations", [])]


