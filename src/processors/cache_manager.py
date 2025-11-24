"""
Sistema de caché para datos meteorológicos.

Este módulo proporciona un sistema de caché usando diskcache para
almacenar respuestas de APIs y evitar exceder límites de tasa.
"""

from typing import Any, Optional, Dict
import logging
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    import diskcache as dc
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    logging.warning("diskcache no está instalado. Usando caché en memoria simple.")

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gestor de caché para datos meteorológicos.

    Implementa una estrategia de caché de dos niveles (si está disponible):
    1. **Persistente (DiskCache)**: Almacena datos en disco (SQLite) para sobrevivir a reinicios.
    2. **Fallback (Memoria)**: Si `diskcache` no está instalado, usa un diccionario en memoria.

    Características:
    - **TTL (Time To Live)**: Expiración automática de datos antiguos.
    - **Límite de Tamaño**: Evita que el caché crezca indefinidamente (LRU policy).
    - **Claves Deterministas**: Genera claves hash MD5 basadas en los parámetros de la petición.
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/cache"),
        ttl_minutes: int = 15,
        max_size: int = 1000,
    ):
        """
        Inicializa el gestor de caché.

        Args:
            cache_dir: Directorio para almacenar el caché
            ttl_minutes: Tiempo de vida del caché en minutos
            max_size: Tamaño máximo del caché en MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_minutes * 60
        self.max_size_mb = max_size

        if DISKCACHE_AVAILABLE:
            self.cache = dc.Cache(
                str(self.cache_dir),
                size_limit=max_size * 1024 * 1024,  # Convertir a bytes
            )
            logger.info(
                f"Caché inicializado: {cache_dir}, TTL: {ttl_minutes} min, "
                f"Tamaño máximo: {max_size} MB"
            )
        else:
            # Fallback a caché simple en memoria
            self.cache = {}
            self._cache_timestamps = {}
            logger.warning(
                "Usando caché en memoria simple. "
                "Instala diskcache para caché persistente."
            )

    def _generate_key(self, source: str, params: Dict[str, Any]) -> str:
        """
        Genera una clave única para el caché.

        Args:
            source: Nombre de la fuente de datos
            params: Parámetros de la petición

        Returns:
            str: Clave única para el caché
        """
        # Crear string estable de los parámetros
        params_str = json.dumps(params, sort_keys=True)
        key_string = f"{source}:{params_str}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(
        self, source: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Obtiene un valor del caché.

        Args:
            source: Nombre de la fuente de datos
            params: Parámetros de la petición original

        Returns:
            Optional[Any]: Valor del caché o None si no existe/expirado
        """
        key = self._generate_key(source, params)

        try:
            if DISKCACHE_AVAILABLE:
                value = self.cache.get(key)
                if value is not None:
                    logger.debug(f"Cache HIT para {source}: {key[:8]}...")
                    return value
            else:
                # Caché en memoria simple
                if key in self.cache:
                    timestamp = self._cache_timestamps.get(key)
                    if timestamp:
                        age = (datetime.now() - timestamp).total_seconds()
                        if age < self.ttl_seconds:
                            logger.debug(f"Cache HIT para {source}: {key[:8]}...")
                            return self.cache[key]
                        else:
                            # Expirado, eliminar
                            del self.cache[key]
                            del self._cache_timestamps[key]

            logger.debug(f"Cache MISS para {source}: {key[:8]}...")
            return None

        except Exception as e:
            logger.error(f"Error al obtener del caché: {e}")
            return None

    def set(
        self, source: str, params: Dict[str, Any], value: Any
    ) -> bool:
        """
        Almacena un valor en el caché.

        Args:
            source: Nombre de la fuente de datos
            params: Parámetros de la petición
            value: Valor a almacenar

        Returns:
            bool: True si se almacenó exitosamente
        """
        key = self._generate_key(source, params)

        try:
            if DISKCACHE_AVAILABLE:
                self.cache.set(key, value, expire=self.ttl_seconds)
            else:
                # Caché en memoria simple
                self.cache[key] = value
                self._cache_timestamps[key] = datetime.now()

            logger.debug(f"Valor almacenado en caché: {source}: {key[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Error al almacenar en caché: {e}")
            return False

    def invalidate(self, source: Optional[str] = None) -> int:
        """
        Invalida entradas del caché.

        Args:
            source: Nombre de la fuente. Si es None, invalida todo

        Returns:
            int: Número de entradas invalidadas
        """
        if DISKCACHE_AVAILABLE:
            if source is None:
                # Limpiar todo
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cache limpiado: {count} entradas eliminadas")
                return count
            else:
                # Limpiar solo entradas de una fuente (más complejo)
                # Por simplicidad, limpiar todo si se especifica fuente
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cache limpiado para {source}: {count} entradas")
                return count
        else:
            if source is None:
                count = len(self.cache)
                self.cache.clear()
                self._cache_timestamps.clear()
                return count
            else:
                # Filtrar por fuente (requiere guardar metadata)
                count = 0
                keys_to_delete = [
                    k for k in self.cache.keys() if k.startswith(source)
                ]
                for key in keys_to_delete:
                    del self.cache[key]
                    if key in self._cache_timestamps:
                        del self._cache_timestamps[key]
                    count += 1
                return count

    def clear(self) -> int:
        """
        Limpia todo el caché.

        Returns:
            int: Número de entradas eliminadas
        """
        return self.invalidate()

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.

        Returns:
            Dict[str, Any]: Estadísticas del caché
        """
        if DISKCACHE_AVAILABLE:
            return {
                "size": len(self.cache),
                "cache_dir": str(self.cache_dir),
                "ttl_seconds": self.ttl_seconds,
                "max_size_mb": self.max_size_mb,
            }
        else:
            return {
                "size": len(self.cache),
                "type": "memory",
                "ttl_seconds": self.ttl_seconds,
            }


