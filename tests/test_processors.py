"""
Tests para los procesadores de datos.
"""

import pytest
import pandas as pd
from datetime import datetime
from src.processors.validators import (
    validate_temperature,
    validate_humidity,
    detect_anomalies,
)
from src.processors.cache_manager import CacheManager
from src.processors.data_processor import DataProcessor


class TestValidators:
    """Tests para validadores."""

    def test_validate_temperature(self):
        assert validate_temperature(25, "Medellín")[0] is True
        assert validate_temperature(100, "Medellín")[0] is False  # Muy caliente
        assert validate_temperature(-100, "Medellín")[0] is False # Muy frío

    def test_validate_humidity(self):
        assert validate_humidity(50)[0] is True
        assert validate_humidity(150)[0] is False
        assert validate_humidity(-10)[0] is False

    def test_detect_anomalies(self):
        data = {
            "temperature": 100, # Anomalía
            "humidity": 50,
            "pressure": 1013,
            "timestamp": datetime.now().isoformat()
        }
        anomalies = detect_anomalies(data, "Medellín")
        assert len(anomalies) > 0
        assert anomalies[0]["field"] == "temperature"


class TestDataProcessor:
    """Tests para DataProcessor."""

    def setup_method(self):
        self.processor = DataProcessor()

    def test_standardize_data_openmeteo(self):
        """Test de estandarización de datos de Open-Meteo."""
        raw_data = {
            "source": "Open-Meteo",
            "temperature": 22.5,
            "humidity": 65,
            "precipitation": 0,
            "wind_speed": 10.5,
            "location": {"lat": 6.2, "lon": -75.5}
        }
        
        standardized = self.processor.standardize_data(raw_data, "Open-Meteo")
        
        assert standardized["source"] == "Open-Meteo"
        assert standardized["temperature"] == 22.5
        assert standardized["humidity"] == 65

    def test_standardize_data_openweather_conversion(self):
        """Test de estandarización con conversión de unidades (OpenWeatherMap)."""
        raw_data = {
            "temperature": 300.15, # Kelvin -> 27.0 C
            "humidity": 60,
            "wind_speed": 10, # m/s -> 36 km/h
            "location": {"lat": 6.2, "lon": -75.5}
        }
        
        standardized = self.processor.standardize_data(raw_data, "OpenWeatherMap")
        
        assert pytest.approx(standardized["temperature"], 0.1) == 27.0
        assert standardized["wind_speed"] == 36.0

    def test_combine_sources(self):
        """Test de combinación de múltiples fuentes."""
        data_list = [
            {"source": "S1", "temperature": 20, "humidity": 60, "location": {}},
            {"source": "S2", "temperature": 22, "humidity": 64, "location": {}},
            {"source": "S3", "temperature": 21, "humidity": 62, "location": {}}
        ]
        
        combined = self.processor.combine_sources(data_list)
        
        assert combined["temperature_mean"] == 21.0
        assert combined["humidity_mean"] == 62.0
        assert combined["temperature_min"] == 20
        assert combined["temperature_max"] == 22
        # Verifica que el valor principal sea el promedio
        assert combined["temperature"] == 21.0

    def test_combine_sources_empty(self):
        """Test de combinación con lista vacía."""
        assert self.processor.combine_sources([]) == {}

    def test_combine_sources_partial_data(self):
        """Test de combinación con datos faltantes."""
        data_list = [
            {"source": "S1", "temperature": 20, "humidity": 60},
            {"source": "S2", "temperature": None, "humidity": 64}, # Sin temp
            {"source": "S3", "temperature": 22, "humidity": None}  # Sin hum
        ]
        
        combined = self.processor.combine_sources(data_list)
        
        assert combined["temperature_mean"] == 21.0 # (20+22)/2
        assert combined["humidity_mean"] == 62.0 # (60+64)/2

    def test_to_dataframe_single(self):
        """Test conversión a DataFrame (dato único)."""
        data = {
            "source": "Test",
            "timestamp": "2023-01-01T12:00:00",
            "temperature": 25.0,
            "humidity": 60
        }
        
        df = self.processor.to_dataframe(data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.index.name == "timestamp"
        assert df.iloc[0]["temperature"] == 25.0

    def test_to_dataframe_forecast(self):
        """Test conversión a DataFrame (pronóstico)."""
        data = {
            "source": "Test",
            "data": {
                "time": ["2023-01-01T12:00", "2023-01-01T13:00"],
                "temperature_2m": [25.0, 26.0]
            }
        }
        
        df = self.processor.to_dataframe(data)
        
        assert len(df) == 2
        assert df.index.name == "time"
        assert "temperature_2m" in df.columns
