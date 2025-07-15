import pytest
from src.investor_intelligence.utils.config import Config, AppConfig


def test_config_initialization():
    """Test that config initializes with default values."""
    config = Config()

    assert config.app.name == "Investor Intelligence Agent"
    assert config.app.version == "1.0.0"
    assert config.mcp.host == "localhost"
    assert config.mcp.port == 8000


def test_app_config():
    """Test AppConfig model."""
    app_config = AppConfig()

    assert app_config.name == "Investor Intelligence Agent"
    assert app_config.version == "1.0.0"
    assert app_config.debug == False
