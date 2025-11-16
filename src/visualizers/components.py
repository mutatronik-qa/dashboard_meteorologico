"""
Componentes reutilizables para visualizaciones.

Este módulo proporciona funciones para crear componentes UI reutilizables
que pueden usarse en diferentes contextos (Streamlit, Jupyter, etc.).
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def create_metric_card(
    label: str,
    value: str,
    unit: str = "",
    icon: str = "",
    color: str = "blue",
) -> Dict[str, Any]:
    """
    Crea una tarjeta de métrica (KPI card).

    Args:
        label: Etiqueta de la métrica
        value: Valor de la métrica
        unit: Unidad de medida
        icon: Emoji o icono
        color: Color del tema

    Returns:
        Dict[str, Any]: Diccionario con información de la tarjeta
    """
    return {
        "label": label,
        "value": value,
        "unit": unit,
        "icon": icon,
        "color": color,
    }


def create_location_selector(
    locations: List[Dict[str, Any]], default: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea un selector de ubicación.

    Args:
        locations: Lista de ubicaciones disponibles
        default: Ubicación por defecto

    Returns:
        Dict[str, Any]: Configuración del selector
    """
    options = [
        {
            "value": loc.get("name", "Desconocido"),
            "label": loc.get("name", "Desconocido"),
            "lat": loc.get("lat"),
            "lon": loc.get("lon"),
        }
        for loc in locations
    ]

    return {
        "options": options,
        "default": default or (options[0]["value"] if options else None),
    }


def create_date_picker(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crea un selector de rango de fechas.

    Args:
        start_date: Fecha de inicio por defecto
        end_date: Fecha de fin por defecto
        min_date: Fecha mínima permitida
        max_date: Fecha máxima permitida

    Returns:
        Dict[str, Any]: Configuración del selector de fechas
    """
    return {
        "start_date": start_date,
        "end_date": end_date,
        "min_date": min_date,
        "max_date": max_date,
    }


def create_legend(
    items: List[Dict[str, Any]], title: str = "Leyenda"
) -> Dict[str, Any]:
    """
    Crea una leyenda para visualizaciones.

    Args:
        items: Lista de items de la leyenda con label y color
        title: Título de la leyenda

    Returns:
        Dict[str, Any]: Configuración de la leyenda
    """
    return {
        "title": title,
        "items": items,
    }


def format_temperature(temp: float, unit: str = "C") -> str:
    """
    Formatea una temperatura para mostrar.

    Args:
        temp: Temperatura
        unit: Unidad (C, F, K)

    Returns:
        str: Temperatura formateada
    """
    if unit == "F":
        temp = (temp * 9 / 5) + 32
        return f"{temp:.1f}°F"
    elif unit == "K":
        temp = temp + 273.15
        return f"{temp:.1f}K"
    else:
        return f"{temp:.1f}°C"


def format_humidity(humidity: float) -> str:
    """
    Formatea la humedad para mostrar.

    Args:
        humidity: Humedad en porcentaje

    Returns:
        str: Humedad formateada
    """
    return f"{humidity:.0f}%"


def format_wind_speed(speed: float, unit: str = "kmh") -> str:
    """
    Formatea la velocidad del viento para mostrar.

    Args:
        speed: Velocidad del viento
        unit: Unidad (kmh, ms, mph)

    Returns:
        str: Velocidad formateada
    """
    if unit == "ms":
        return f"{speed:.1f} m/s"
    elif unit == "mph":
        speed = speed * 0.621371
        return f"{speed:.1f} mph"
    else:
        return f"{speed:.1f} km/h"


