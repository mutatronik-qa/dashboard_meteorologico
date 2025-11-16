"""
Funciones de visualización para datos meteorológicos.

Este módulo proporciona funciones para crear gráficos y mapas usando
Plotly, Folium y otras librerías de visualización.
"""

from typing import Dict, Any, List, Optional
import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    logging.warning("folium no está instalado. Mapas no disponibles.")

logger = logging.getLogger(__name__)


def create_temperature_map(
    data: List[Dict[str, Any]],
    center_lat: float = 6.2442,
    center_lon: float = -75.5812,
    zoom: int = 10,
) -> Any:
    """
    Crea un mapa de temperatura usando Folium.

    Args:
        data: Lista de diccionarios con datos de ubicaciones
        center_lat: Latitud del centro del mapa
        center_lon: Longitud del centro del mapa
        zoom: Nivel de zoom

    Returns:
        folium.Map: Mapa con marcadores de temperatura
    """
    if not FOLIUM_AVAILABLE:
        logger.warning("folium no disponible. Retornando None.")
        return None

    logger.info(f"Creando mapa de temperatura con {len(data)} ubicaciones")

    # Crear mapa base
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)

    # Agregar marcadores para cada ubicación
    for item in data:
        location = item.get("location", {})
        lat = location.get("lat")
        lon = location.get("lon")
        temp = item.get("temperature")

        if lat and lon and temp is not None:
            # Color según temperatura
            if temp < 15:
                color = "blue"
            elif temp < 20:
                color = "green"
            elif temp < 25:
                color = "orange"
            else:
                color = "red"

            popup_text = (
                f"<b>{location.get('name', 'Ubicación')}</b><br>"
                f"Temperatura: {temp:.1f}°C<br>"
                f"Humedad: {item.get('humidity', 'N/A')}%"
            )

            folium.Marker(
                [lat, lon],
                popup=popup_text,
                icon=folium.Icon(color=color, icon="thermometer-half"),
            ).add_to(m)

    return m


def create_comparison_chart(
    data: List[Dict[str, Any]], metric: str = "temperature"
) -> go.Figure:
    """
    Crea un gráfico de barras comparando métricas entre ubicaciones.

    Args:
        data: Lista de diccionarios con datos de ubicaciones
        metric: Métrica a comparar (temperature, humidity, etc.)

    Returns:
        go.Figure: Gráfico de barras
    """
    logger.info(f"Creando gráfico de comparación para {metric}")

    locations = []
    values = []

    for item in data:
        location = item.get("location", {})
        location_name = location.get("name", "Desconocido")
        value = item.get(metric)

        if value is not None:
            locations.append(location_name)
            values.append(value)

    fig = go.Figure(
        data=[
            go.Bar(
                x=locations,
                y=values,
                marker_color="steelblue",
                text=[f"{v:.1f}" for v in values],
                textposition="auto",
            )
        ]
    )

    metric_labels = {
        "temperature": "Temperatura (°C)",
        "humidity": "Humedad (%)",
        "precipitation": "Precipitación (mm)",
        "wind_speed": "Velocidad del Viento (km/h)",
    }

    fig.update_layout(
        title=f"Comparación de {metric_labels.get(metric, metric)}",
        xaxis_title="Ubicación",
        yaxis_title=metric_labels.get(metric, metric),
        showlegend=False,
    )

    return fig


def create_time_series(
    df: pd.DataFrame, metric: str = "temperature", title: Optional[str] = None
) -> go.Figure:
    """
    Crea un gráfico de serie temporal.

    Args:
        df: DataFrame con datos temporales
        metric: Métrica a graficar
        title: Título del gráfico

    Returns:
        go.Figure: Gráfico de línea temporal
    """
    logger.info(f"Creando serie temporal para {metric}")

    if metric not in df.columns:
        logger.warning(f"Columna {metric} no encontrada en DataFrame")
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[metric],
            mode="lines+markers",
            name=metric,
            line=dict(color="steelblue", width=2),
        )
    )

    metric_labels = {
        "temperature": "Temperatura (°C)",
        "humidity": "Humedad (%)",
        "precipitation": "Precipitación (mm)",
        "wind_speed": "Velocidad del Viento (km/h)",
    }

    fig.update_layout(
        title=title or f"Serie Temporal - {metric_labels.get(metric, metric)}",
        xaxis_title="Fecha y Hora",
        yaxis_title=metric_labels.get(metric, metric),
        hovermode="x unified",
    )

    return fig


def create_humidity_chart(
    data: List[Dict[str, Any]], chart_type: str = "bar"
) -> go.Figure:
    """
    Crea un gráfico de humedad.

    Args:
        data: Lista de diccionarios con datos
        chart_type: Tipo de gráfico (bar, line, pie)

    Returns:
        go.Figure: Gráfico de humedad
    """
    logger.info(f"Creando gráfico de humedad tipo {chart_type}")

    locations = []
    values = []

    for item in data:
        location = item.get("location", {})
        location_name = location.get("name", "Desconocido")
        humidity = item.get("humidity")

        if humidity is not None:
            locations.append(location_name)
            values.append(humidity)

    if chart_type == "bar":
        fig = go.Figure(
            data=[
                go.Bar(
                    x=locations,
                    y=values,
                    marker_color="lightblue",
                    text=[f"{v:.1f}%" for v in values],
                    textposition="auto",
                )
            ]
        )
    elif chart_type == "pie":
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=locations,
                    values=values,
                    hole=0.3,
                )
            ]
        )
    else:  # line
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=locations,
                    y=values,
                    mode="lines+markers",
                    line=dict(color="lightblue", width=2),
                )
            ]
        )

    fig.update_layout(
        title="Humedad Relativa por Ubicación",
        xaxis_title="Ubicación",
        yaxis_title="Humedad (%)",
    )

    return fig


def create_wind_chart(
    data: List[Dict[str, Any]], chart_type: str = "polar"
) -> go.Figure:
    """
    Crea un gráfico de viento (rosa de vientos o vectorial).

    Args:
        data: Lista de diccionarios con datos
        chart_type: Tipo de gráfico (polar, bar)

    Returns:
        go.Figure: Gráfico de viento
    """
    logger.info(f"Creando gráfico de viento tipo {chart_type}")

    if chart_type == "polar":
        # Rosa de vientos
        speeds = []
        directions = []

        for item in data:
            speed = item.get("wind_speed")
            direction = item.get("wind_direction")

            if speed is not None and direction is not None:
                speeds.append(speed)
                directions.append(direction)

        if speeds:
            fig = go.Figure(
                data=go.Scatterpolar(
                    r=speeds,
                    theta=directions,
                    mode="markers",
                    marker=dict(size=10, color=speeds, colorscale="Viridis"),
                )
            )

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, max(speeds) * 1.1]),
                    angularaxis=dict(
                        tickmode="array",
                        tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                        ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                    ),
                ),
                title="Rosa de Vientos",
            )
        else:
            fig = go.Figure()
    else:
        # Gráfico de barras simple
        locations = []
        speeds = []

        for item in data:
            location = item.get("location", {})
            location_name = location.get("name", "Desconocido")
            speed = item.get("wind_speed")

            if speed is not None:
                locations.append(location_name)
                speeds.append(speed)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=locations,
                    y=speeds,
                    marker_color="lightgreen",
                    text=[f"{v:.1f} km/h" for v in speeds],
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="Velocidad del Viento por Ubicación",
            xaxis_title="Ubicación",
            yaxis_title="Velocidad (km/h)",
        )

    return fig


def create_metrics(
    data: Dict[str, Any], metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Crea tarjetas de métricas (KPIs).

    Args:
        data: Diccionario con datos meteorológicos
        metrics: Lista de métricas a incluir (None = todas)

    Returns:
        Dict[str, Any]: Diccionario con métricas formateadas
    """
    if metrics is None:
        metrics = ["temperature", "humidity", "precipitation", "wind_speed"]

    result = {}

    metric_configs = {
        "temperature": {
            "label": "Temperatura",
            "unit": "°C",
            "format": "{:.1f}",
            "icon": "🌡️",
        },
        "humidity": {
            "label": "Humedad",
            "unit": "%",
            "format": "{:.0f}",
            "icon": "💧",
        },
        "precipitation": {
            "label": "Precipitación",
            "unit": "mm",
            "format": "{:.1f}",
            "icon": "🌧️",
        },
        "wind_speed": {
            "label": "Viento",
            "unit": "km/h",
            "format": "{:.1f}",
            "icon": "💨",
        },
    }

    for metric in metrics:
        if metric in data and data[metric] is not None:
            config = metric_configs.get(metric, {})
            value = data[metric]
            formatted_value = config.get("format", "{}").format(value)

            result[metric] = {
                "label": config.get("label", metric),
                "value": formatted_value,
                "unit": config.get("unit", ""),
                "icon": config.get("icon", ""),
                "raw_value": value,
            }

    return result


