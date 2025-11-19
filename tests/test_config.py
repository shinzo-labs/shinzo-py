"""Tests for configuration validation."""

import pytest
from shinzo.config import ConfigValidator
from shinzo.types import TelemetryConfig, AuthConfig


def test_valid_config() -> None:
    """Test that a valid configuration passes validation."""
    config = TelemetryConfig(server_name="test-server", server_version="1.0.0")
    ConfigValidator.validate(config)  # Should not raise


def test_missing_server_name() -> None:
    """Test that missing server_name raises ValueError."""
    with pytest.raises(ValueError, match="server_name is required"):
        config = TelemetryConfig(server_name="", server_version="1.0.0")
        ConfigValidator.validate(config)


def test_invalid_sampling_rate() -> None:
    """Test that invalid sampling_rate raises ValueError."""
    with pytest.raises(ValueError, match="sampling_rate must be between"):
        config = TelemetryConfig(
            server_name="test-server", server_version="1.0.0", sampling_rate=1.5
        )
        ConfigValidator.validate(config)


def test_bearer_auth_without_token() -> None:
    """Test that bearer auth without token raises ValueError."""
    with pytest.raises(ValueError, match="token is required"):
        config = TelemetryConfig(
            server_name="test-server",
            server_version="1.0.0",
            exporter_auth=AuthConfig(type="bearer"),
        )
        ConfigValidator.validate(config)


def test_basic_auth_without_credentials() -> None:
    """Test that basic auth without credentials raises ValueError."""
    with pytest.raises(ValueError, match="username and password are required"):
        config = TelemetryConfig(
            server_name="test-server",
            server_version="1.0.0",
            exporter_auth=AuthConfig(type="basic", username="user"),
        )
        ConfigValidator.validate(config)
