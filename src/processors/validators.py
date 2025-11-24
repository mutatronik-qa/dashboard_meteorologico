"""
Validadores de datos meteorológicos.

Este módulo actúa como una capa de "Calidad de Datos" (Data Quality).
Su objetivo es asegurar que los datos que entran al sistema sean físicamente posibles
y consistentes.

Funciones principales:
- Validación de rangos físicos (ej. humedad 0-100%).
- Detección de anomalías contextuales (ej. temperatura extrema para Medellín).
- Validación de tipos de datos y timestamps.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def validate_temperature(
    temperature: float, location: str = "Medellín"
) -> Tuple[bool, Optional[str]]:
    """
    Valida que la temperatura esté en un rango razonable.

    Para Medellín, el rango típico es -50 a 60°C, aunque valores
    extremos son raros.

    Args:
        temperature: Temperatura en grados Celsius
        location: Nombre de la ubicación (para logging)

    Returns:
        Tuple[bool, Optional[str]]: (es_válida, mensaje_error)
    """
    if temperature is None:
        return False, "Temperatura es None"

    if not isinstance(temperature, (int, float)):
        return False, f"Temperatura debe ser numérica, recibido: {type(temperature)}"

    if temperature < -50 or temperature > 60:
        return (
            False,
            f"Temperatura fuera de rango válido: {temperature}°C "
            f"(rango esperado: -50 a 60°C)",
        )

    # Rango más estricto para Medellín (típicamente 10-30°C)
    if location == "Medellín" and (temperature < 5 or temperature > 35):
        logger.warning(
            f"Temperatura inusual para {location}: {temperature}°C "
            f"(rango típico: 5-35°C)"
        )

    return True, None


def validate_humidity(humidity: float) -> Tuple[bool, Optional[str]]:
    """
    Valida que la humedad esté en el rango 0-100%.

    Args:
        humidity: Humedad relativa en porcentaje

    Returns:
        Tuple[bool, Optional[str]]: (es_válida, mensaje_error)
    """
    if humidity is None:
        return False, "Humedad es None"

    if not isinstance(humidity, (int, float)):
        return False, f"Humedad debe ser numérica, recibido: {type(humidity)}"

    if humidity < 0 or humidity > 100:
        return (
            False,
            f"Humedad fuera de rango válido: {humidity}% "
            f"(rango esperado: 0-100%)",
        )

    return True, None


def validate_pressure(
    pressure: float, unit: str = "hPa"
) -> Tuple[bool, Optional[str]]:
    """
    Valida que la presión atmosférica esté en un rango razonable.

    Args:
        pressure: Presión atmosférica
        unit: Unidad de presión (hPa, Pa, mmHg, inHg)

    Returns:
        Tuple[bool, Optional[str]]: (es_válida, mensaje_error)
    """
    if pressure is None:
        return False, "Presión es None"

    if not isinstance(pressure, (int, float)):
        return False, f"Presión debe ser numérica, recibido: {type(pressure)}"

    # Convertir a hPa para validación
    if unit == "Pa":
        pressure_hpa = pressure / 100
    elif unit == "mmHg":
        pressure_hpa = pressure * 1.33322
    elif unit == "inHg":
        pressure_hpa = pressure * 33.8639
    else:  # hPa por defecto
        pressure_hpa = pressure

    # Rango válido: 800-1100 hPa (cubre desde nivel del mar hasta ~2000m)
    if pressure_hpa < 800 or pressure_hpa > 1100:
        return (
            False,
            f"Presión fuera de rango válido: {pressure} {unit} "
            f"(rango esperado: 800-1100 hPa)",
        )

    return True, None


def validate_timestamp(
    timestamp: Any, format: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[datetime]]:
    """
    Valida y convierte un timestamp a datetime.

    Args:
        timestamp: Timestamp a validar (str, datetime, int, float)
        format: Formato de string (si timestamp es str)

    Returns:
        Tuple[bool, Optional[str], Optional[datetime]]:
            (es_válida, mensaje_error, datetime_obj)
    """
    if timestamp is None:
        return False, "Timestamp es None", None

    try:
        if isinstance(timestamp, datetime):
            return True, None, timestamp
        elif isinstance(timestamp, str):
            if format:
                dt = datetime.strptime(timestamp, format)
            else:
                # Intentar parseo automático
                dt = pd.to_datetime(timestamp)
            return True, None, dt
        elif isinstance(timestamp, (int, float)):
            # Asumir timestamp Unix
            dt = datetime.fromtimestamp(timestamp)
            return True, None, dt
        else:
            return (
                False,
                f"Formato de timestamp no soportado: {type(timestamp)}",
                None,
            )
    except (ValueError, TypeError, OSError) as e:
        return False, f"Error al parsear timestamp: {e}", None


def detect_anomalies(
    data: Dict[str, Any], location: str = "Medellín"
) -> List[Dict[str, Any]]:
    """
    Detecta anomalías en los datos meteorológicos.

    Args:
        data: Diccionario con datos meteorológicos
        location: Nombre de la ubicación

    Returns:
        List[Dict[str, Any]]: Lista de anomalías detectadas
    """
    anomalies = []

    # Validar temperatura
    if "temperature" in data:
        is_valid, error = validate_temperature(data["temperature"], location)
        if not is_valid:
            anomalies.append(
                {
                    "field": "temperature",
                    "value": data["temperature"],
                    "error": error,
                    "severity": "error" if "None" in str(error) else "warning",
                }
            )

    # Validar humedad
    if "humidity" in data:
        is_valid, error = validate_humidity(data["humidity"])
        if not is_valid:
            anomalies.append(
                {
                    "field": "humidity",
                    "value": data["humidity"],
                    "error": error,
                    "severity": "error",
                }
            )

    # Validar presión
    if "pressure" in data:
        is_valid, error = validate_pressure(data["pressure"])
        if not is_valid:
            anomalies.append(
                {
                    "field": "pressure",
                    "value": data["pressure"],
                    "error": error,
                    "severity": "error",
                }
            )

    # Validar timestamp
    if "timestamp" in data:
        is_valid, error, _ = validate_timestamp(data["timestamp"])
        if not is_valid:
            anomalies.append(
                {
                    "field": "timestamp",
                    "value": data["timestamp"],
                    "error": error,
                    "severity": "error",
                }
            )

    # Detectar valores faltantes críticos
    critical_fields = ["temperature", "humidity"]
    for field in critical_fields:
        if field not in data or data[field] is None:
            anomalies.append(
                {
                    "field": field,
                    "value": None,
                    "error": f"Campo crítico '{field}' faltante",
                    "severity": "error",
                }
            )

    # Detectar valores extremos pero posibles
    if "temperature" in data and data["temperature"] is not None:
        temp = data["temperature"]
        if temp < 0 or temp > 30:
            anomalies.append(
                {
                    "field": "temperature",
                    "value": temp,
                    "error": f"Temperatura extrema para {location}: {temp}°C",
                    "severity": "warning",
                }
            )

    if anomalies:
        logger.warning(f"Se detectaron {len(anomalies)} anomalías en los datos")

    return anomalies


