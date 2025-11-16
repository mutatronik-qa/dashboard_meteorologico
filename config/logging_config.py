"""
Configuración de logging para el proyecto.

Este módulo configura el sistema de logging con niveles DEBUG, INFO,
WARNING, ERROR, y CRITICAL. Los logs se escriben tanto a archivo
como a consola con formato completo.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    debug_mode: bool = False,
) -> logging.Logger:
    """
    Configura el sistema de logging.

    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta al archivo de log. Si es None, no se escribe a archivo
        debug_mode: Si es True, activa modo debug con más información

    Returns:
        logging.Logger: Logger configurado
    """
    # Convertir nivel de string a constante de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Crear logger principal
    logger = logging.getLogger("dashboard_meteorologico")
    logger.setLevel(numeric_level)

    # Evitar duplicar handlers si ya están configurados
    if logger.handlers:
        return logger

    # Formato detallado para archivo
    file_formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Formato más simple para consola
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Handler para archivo
    if log_file:
        # Crear directorio de logs si no existe
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Siempre DEBUG en archivo
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Configurar logging de librerías externas
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    if debug_mode:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    logger.info(f"Logging configurado - Nivel: {log_level}, Archivo: {log_file}")

    return logger


