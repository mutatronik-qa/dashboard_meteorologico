"""
Tests para los procesadores de datos.
"""

import pytest
from src.processors.validators import (
    validate_temperature,
    validate_humidity,
    validate_pressure,
    detect_anomalies,
)
from src.processors.cache_manager import CacheManager
from src.processors.data_processor import DataProcessor
from pathlib import Path


class TestValidators:
    """Tests para validadores."""

    def test_validate_temperature_valid(self):
        """Test de temperatura válida."""
        is_valid, error = validate_temperature(22.5, "Medellín")
        assert is_valid is True
        assert error is None

    def test_validate_temperature_invalid(self):
        """Test de temperatura inválida."""
        is_valid, error = validate_temperature(100, "Medellín")
        assert is_valid is False
        assert error is not None

    def test_validate_humidity_valid(self):
        """Test de humedad válida."""
        is_valid, error = validate_humidity(65)
        assert is_valid is True
        assert error is None

    def test_validate_humidity_invalid(self):
        """Test de humedad inválida."""
        is_valid, error = validate_humidity(150)
        assert is_valid is False
        assert error is not None

    def test_detect_anomalies(self):
        """Test de detección de anomalías."""
        data = {
            "temperature": 22.5,
            "humidity": 65,
            "pressure": 1013.25,
            "timestamp": "2024-01-15T12:00:00",
        }
        anomalies = detect_anomalies(data, "Medellín")
        assert isinstance(anomalies, list)


class TestCacheManager:
    """Tests para CacheManager."""

    def test_init(self, tmp_path):
        """Test de inicialización."""
        cache_dir = tmp_path / "cache"
        cache = CacheManager(cache_dir=cache_dir, ttl_minutes=15)
        assert cache.cache_dir == cache_dir
        assert cache.ttl_seconds == 15 * 60

    def test_set_and_get(self, tmp_path):
        """Test de almacenar y obtener del caché."""
        cache_dir = tmp_path / "cache"
        cache = CacheManager(cache_dir=cache_dir, ttl_minutes=15)

        test_data = {"test": "data"}
        cache.set("test_source", {"param": "value"}, test_data)

        retrieved = cache.get("test_source", {"param": "value"})
        assert retrieved == test_data

    def test_clear(self, tmp_path):
        """Test de limpiar caché."""
        cache_dir = tmp_path / "cache"
        cache = CacheManager(cache_dir=cache_dir)

        cache.set("test_source", {"param": "value"}, {"data": "test"})
        count = cache.clear()
        assert count >= 0


class TestDataProcessor:
    """Tests para DataProcessor."""

    def test_init(self):
        """Test de inicialización."""
        processor = DataProcessor()
        assert processor is not None

    def test_standardize_data(self):
        """Test de estandarización de datos."""
        processor = DataProcessor()

        raw_data = {
            "temperature": 22.5,
            "humidity": 65,
            "location": {"lat": 6.2442, "lon": -75.5812},
        }

        standardized = processor.standardize_data(raw_data, "TestSource")
        assert standardized["source"] == "TestSource"
        assert "temperature" in standardized

    def test_combine_sources(self):
        """Test de combinación de fuentes."""
        processor = DataProcessor()

        data_list = [
            {"source": "Source1", "temperature": 20, "humidity": 60},
            {"source": "Source2", "temperature": 22, "humidity": 65},
        ]

        combined = processor.combine_sources(data_list)
        assert "temperature_mean" in combined
        assert combined["temperature_mean"] == 21.0


