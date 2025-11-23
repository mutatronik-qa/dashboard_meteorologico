"""
Tests para la API IoT.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.api.main import app

client = TestClient(app)

class TestIoTAPI:
    """Tests para los endpoints de la API."""

    def test_health_check(self):
        """Test del endpoint de salud."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "1.0.0"}

    @patch("src.api.main.get_sources")
    @patch("src.processors.data_processor.DataProcessor.standardize_data")
    @patch("src.processors.data_processor.DataProcessor.combine_sources")
    @patch("src.processors.data_processor.DataProcessor.validate_and_clean")
    def test_get_current_weather_success(
        self, 
        mock_validate, 
        mock_combine, 
        mock_standardize, 
        mock_get_sources
    ):
        """Test de obtención de clima actual exitosa."""
        # Mock sources
        mock_source = Mock()
        mock_source.name = "Test-Source"
        mock_source.get_current_weather.return_value = {"temp": 25}
        mock_get_sources.return_value = [mock_source]

        # Mock processor methods
        mock_standardize.return_value = {"source": "Test-Source", "temperature": 25}
        mock_combine.return_value = {"temperature": 25}
        mock_validate.return_value = {"temperature": 25, "location": "Medellín"}

        response = client.get("/weather/current/Medellín?lat=6.2&lon=-75.5")
        
        assert response.status_code == 200
        assert response.json()["temperature"] == 25

    @patch("src.api.main.get_sources")
    def test_get_current_weather_no_sources(self, mock_get_sources):
        """Test cuando no hay fuentes disponibles."""
        mock_get_sources.return_value = []
        
        response = client.get("/weather/current/Medellín?lat=6.2&lon=-75.5")
        
        assert response.status_code == 503

    @patch("src.api.main.OpenMeteoSource")
    def test_get_forecast_success(self, mock_source_cls):
        """Test de obtención de pronóstico exitosa."""
        mock_source = mock_source_cls.return_value
        mock_source.get_forecast.return_value = {
            "hourly": {"time": [], "temperature_2m": []}
        }

        response = client.get("/weather/forecast/Medellín?lat=6.2&lon=-75.5&days=3")
        
        assert response.status_code == 200
        assert "hourly" in response.json()

    def test_get_forecast_invalid_days(self):
        """Test de validación de días."""
        response = client.get("/weather/forecast/Medellín?lat=6.2&lon=-75.5&days=100")
        assert response.status_code == 422  # Validation Error
