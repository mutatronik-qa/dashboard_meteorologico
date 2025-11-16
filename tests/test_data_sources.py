"""
Tests para las fuentes de datos meteorológicos.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.data_sources import (
    OpenMeteoSource,
    OpenWeatherSource,
    BaseWeatherSource,
)


class TestOpenMeteoSource:
    """Tests para OpenMeteoSource."""

    def test_init(self):
        """Test de inicialización."""
        source = OpenMeteoSource()
        assert source.name == "Open-Meteo"
        assert source.api_key is None

    @patch("src.data_sources.openmeteo.requests.Session")
    def test_get_current_weather(self, mock_session):
        """Test de obtención de clima actual."""
        # Mock de respuesta
        mock_response = Mock()
        mock_response.json.return_value = {
            "current": {
                "temperature_2m": 22.5,
                "relative_humidity_2m": 65,
                "precipitation": 0,
                "wind_speed_10m": 10.5,
            }
        }
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        source = OpenMeteoSource()
        source.session = mock_session_instance

        data = source.get_current_weather(6.2442, -75.5812)

        assert data["source"] == "Open-Meteo"
        assert "temperature" in data
        assert "humidity" in data


class TestOpenWeatherSource:
    """Tests para OpenWeatherSource."""

    def test_init_without_key(self):
        """Test que requiere API key."""
        with pytest.raises(ValueError):
            OpenWeatherSource(api_key="")

    def test_init_with_key(self):
        """Test de inicialización con API key."""
        source = OpenWeatherSource(api_key="test_key")
        assert source.name == "OpenWeatherMap"
        assert source.api_key == "test_key"


class TestBaseWeatherSource:
    """Tests para BaseWeatherSource."""

    def test_is_available(self):
        """Test de verificación de disponibilidad."""
        # Crear una subclase concreta para testing
        class TestSource(BaseWeatherSource):
            def get_current_weather(self, lat, lon, **kwargs):
                return {}

            def get_forecast(self, lat, lon, days=5, **kwargs):
                return {}

        source = TestSource("Test", "https://example.com")
        # Mock de la petición
        with patch.object(source, "_make_request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            assert source.is_available() is True


