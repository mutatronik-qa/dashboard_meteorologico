"""
Script principal del dashboard meteorológico.

Este script actúa como el punto de entrada para la interfaz de línea de comandos (CLI).
Su función es orquestar la interacción con el usuario, inicializar los componentes
del sistema (fuentes de datos, procesadores, dashboard) y presentar los resultados
en la terminal de manera visual usando la librería 'rich'.

Flujo principal:
1. Parseo de argumentos de línea de comandos.
2. Configuración del sistema de logging.
3. Carga de configuración y ubicaciones.
4. Inicialización de fuentes de datos (OpenMeteo, OpenWeather, etc.).
5. Ejecución de la acción solicitada (listar, obtener clima actual, pronóstico).
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings, setup_logging, load_locations
from src.data_sources import (
    OpenMeteoSource,
    OpenWeatherSource,
    MeteosourceSource,
    MeteoBlueSource,
    SIATASource,
    RadarIDEAMSource,
)
from src.processors import CacheManager, DataProcessor
from src.visualizers.dashboard import Dashboard
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def create_sources(settings) -> list:
    """
    Crea e inicializa las instancias de todas las fuentes de datos disponibles.
    
    Esta función verifica qué API keys están configuradas en los settings y
    crea las instancias correspondientes. Open-Meteo y SIATA se inicializan
    siempre ya que no requieren autenticación (o su manejo es interno).

    Args:
        settings: Objeto de configuración con las credenciales y parámetros.

    Returns:
        list: Lista de objetos que heredan de BaseWeatherSource, listos para usar.
    """
    sources = []

    # Open-Meteo (siempre disponible, sin API key)
    try:
        sources.append(OpenMeteoSource())
        console.print("[green]✓[/green] Open-Meteo inicializado")
    except Exception as e:
        console.print(f"[red]✗[/red] Error al inicializar Open-Meteo: {e}")

    # OpenWeatherMap
    if settings.openweather_api_key:
        try:
            sources.append(
                OpenWeatherSource(api_key=settings.openweather_api_key)
            )
            console.print("[green]✓[/green] OpenWeatherMap inicializado")
        except Exception as e:
            console.print(
                f"[yellow]⚠[/yellow] Error al inicializar OpenWeatherMap: {e}"
            )

    # Meteosource
    if settings.meteosource_api_key:
        try:
            sources.append(
                MeteosourceSource(api_key=settings.meteosource_api_key)
            )
            console.print("[green]✓[/green] Meteosource inicializado")
        except Exception as e:
            console.print(
                f"[yellow]⚠[/yellow] Error al inicializar Meteosource: {e}"
            )

    # MeteoBlue
    if settings.meteoblue_api_key:
        try:
            sources.append(
                MeteoBlueSource(api_key=settings.meteoblue_api_key)
            )
            console.print("[green]✓[/green] MeteoBlue inicializado")
        except Exception as e:
            console.print(
                f"[yellow]⚠[/yellow] Error al inicializar MeteoBlue: {e}"
            )

    # SIATA
    try:
        sources.append(SIATASource())
        console.print("[green]✓[/green] SIATA inicializado")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Error al inicializar SIATA: {e}")

    # Radar IDEAM
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        try:
            sources.append(
                RadarIDEAMSource(
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
            )
            console.print("[green]✓[/green] Radar IDEAM inicializado")
        except Exception as e:
            console.print(
                f"[yellow]⚠[/yellow] Error al inicializar Radar IDEAM: {e}"
            )

    return sources


def print_weather_data(data: dict, location_name: str):
    """
    Imprime los datos meteorológicos en formato tabular.

    Args:
        data: Diccionario con datos meteorológicos
        location_name: Nombre de la ubicación
    """
    table = Table(title=f"Datos Meteorológicos - {location_name}")

    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="magenta")
    table.add_column("Unidad", style="green")

    if "temperature" in data:
        table.add_row("🌡️ Temperatura", f"{data['temperature']:.1f}", "°C")
    if "humidity" in data:
        table.add_row("💧 Humedad", f"{data['humidity']:.0f}", "%")
    if "precipitation" in data:
        table.add_row("🌧️ Precipitación", f"{data['precipitation']:.1f}", "mm")
    if "wind_speed" in data:
        table.add_row("💨 Viento", f"{data['wind_speed']:.1f}", "km/h")
    if "pressure" in data:
        table.add_row("📊 Presión", f"{data['pressure']:.1f}", "hPa")

    console.print(table)


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Dashboard Meteorológico - CLI"
    )
    parser.add_argument(
        "--location",
        type=str,
        help="Nombre de la ubicación (por defecto: Medellín)",
        default="Medellín",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Fuente de datos específica (opcional)",
    )
    parser.add_argument(
        "--forecast",
        type=int,
        help="Obtener pronóstico para N días",
    )
    parser.add_argument(
        "--list-locations",
        action="store_true",
        help="Listar ubicaciones disponibles",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Listar fuentes de datos disponibles",
    )

    args = parser.parse_args()

    # Configurar logging
    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        debug_mode=settings.debug_mode,
    )

    console.print(
        Panel.fit(
            "[bold blue]Dashboard Meteorológico[/bold blue]",
            border_style="blue",
        )
    )

    # Listar ubicaciones
    if args.list_locations:
        locations = load_locations()
        table = Table(title="Ubicaciones Disponibles")
        table.add_column("Nombre", style="cyan")
        table.add_column("Latitud", style="magenta")
        table.add_column("Longitud", style="magenta")
        table.add_column("Altitud", style="green")

        for loc in locations:
            table.add_row(
                loc.name,
                f"{loc.lat:.4f}",
                f"{loc.lon:.4f}",
                f"{loc.altitude or 'N/A'} m",
            )

        console.print(table)
        return

    # Crear fuentes de datos
    console.print("\n[bold]Inicializando fuentes de datos...[/bold]")
    sources = create_sources(settings)

    if not sources:
        console.print(
            "[red]Error: No hay fuentes de datos disponibles[/red]"
        )
        sys.exit(1)

    # Listar fuentes
    if args.list_sources:
        table = Table(title="Fuentes de Datos Disponibles")
        table.add_column("Fuente", style="cyan")
        table.add_column("Estado", style="green")

        for source in sources:
            status = "✓ Disponible" if source.is_available() else "✗ No disponible"
            table.add_row(source.name, status)

        console.print(table)
        return

    # Cargar ubicaciones
    locations = load_locations()
    location = next(
        (loc for loc in locations if loc.name == args.location), None
    )

    if not location:
        console.print(
            f"[red]Error: Ubicación '{args.location}' no encontrada[/red]"
        )
        console.print("Usa --list-locations para ver ubicaciones disponibles")
        sys.exit(1)

    # Crear dashboard
    # El CacheManager se encarga de persistir datos para evitar llamadas excesivas a APIs
    cache_manager = CacheManager(
        cache_dir=settings.cache_dir, ttl_minutes=settings.cache_ttl_minutes
    )
    # El DataProcessor normaliza los datos de diferentes fuentes a un formato común
    processor = DataProcessor(cache_manager=cache_manager)
    # El Dashboard coordina la obtención y visualización
    dashboard = Dashboard(sources, processor=processor, cache_manager=cache_manager)

    # Obtener datos
    console.print(f"\n[bold]Obteniendo datos para {location.name}...[/bold]")

    try:
        if args.forecast:
            # Obtener pronóstico
            source_name = args.source if args.source else None
            forecast_data = dashboard.get_forecast_for_location(
                location.lat,
                location.lon,
                days=args.forecast,
                source_name=source_name,
            )
            console.print(
                f"[green]✓[/green] Pronóstico obtenido de "
                f"{forecast_data.get('source', 'fuente desconocida')}"
            )
        else:
            # Obtener datos actuales
            source_names = [args.source] if args.source else None
            data_list = dashboard.get_data_for_location(
                location.lat,
                location.lon,
                source_names=source_names,
            )

            if data_list:
                # Combinar datos de múltiples fuentes
                combined = processor.combine_sources(data_list)
                print_weather_data(combined, location.name)

                console.print(
                    f"\n[green]✓[/green] Datos obtenidos de "
                    f"{len(data_list)} fuente(s)"
                )
            else:
                console.print("[red]No se pudieron obtener datos[/red]")
                sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()


