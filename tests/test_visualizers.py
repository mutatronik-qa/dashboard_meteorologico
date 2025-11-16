"""
Tests para los visualizadores.
"""

import pytest
from src.visualizers.plots import (
    create_comparison_chart,
    create_metrics,
)
from src.visualizers.components import (
    create_metric_card,
    format_temperature,
)


class TestPlots:
    """Tests para funciones de gráficos."""

    def test_create_comparison_chart(self):
        """Test de creación de gráfico de comparación."""
        data = [
            {
                "location": {"name": "Medellín"},
                "temperature": 22.5,
            },
            {
                "location": {"name": "Bello"},
                "temperature": 23.0,
            },
        ]

        fig = create_comparison_chart(data, metric="temperature")
        assert fig is not None

    def test_create_metrics(self):
        """Test de creación de métricas."""
        data = {
            "temperature": 22.5,
            "humidity": 65,
            "precipitation": 0,
            "wind_speed": 10.5,
        }

        metrics = create_metrics(data)
        assert "temperature" in metrics
        assert metrics["temperature"]["value"] == "22.5"


class TestComponents:
    """Tests para componentes."""

    def test_create_metric_card(self):
        """Test de creación de tarjeta de métrica."""
        card = create_metric_card(
            label="Temperatura",
            value="22.5",
            unit="°C",
            icon="🌡️",
        )
        assert card["label"] == "Temperatura"
        assert card["value"] == "22.5"

    def test_format_temperature(self):
        """Test de formateo de temperatura."""
        formatted = format_temperature(22.5, "C")
        assert "22.5" in formatted
        assert "°C" in formatted


