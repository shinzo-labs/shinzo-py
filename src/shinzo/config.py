"""Configuration validation for Shinzo."""

from typing import Any, Dict
from shinzo.types import TelemetryConfig


DEFAULT_CONFIG: Dict[str, Any] = {
    "exporter_endpoint": "https://api.app.shinzo.ai/telemetry/ingest_http",
    "sampling_rate": 1.0,
    "metric_export_interval_ms": 60000,
    "enable_pii_sanitization": False,
    "enable_argument_collection": True,
    "exporter_type": "otlp-http",
    "enable_metrics": True,
    "enable_tracing": True,
    "batch_timeout_ms": 30000,
}

class ConfigValidator:
    """Validator for telemetry configuration."""

    @staticmethod
    def validate(config: TelemetryConfig) -> None:
        """
        Validate the telemetry configuration.

        Args:
            config: The configuration to validate

        Raises:
            ValueError: If the configuration is invalid
        """
        if not config.server_name:
            raise ValueError("server_name is required")

        if not config.server_version:
            raise ValueError("server_version is required")

        if config.sampling_rate is not None:
            if not 0.0 <= config.sampling_rate <= 1.0:
                raise ValueError("sampling_rate must be between 0.0 and 1.0")

        if config.exporter_auth:
            auth = config.exporter_auth
            if auth.type == "bearer" and not auth.token:
                raise ValueError("token is required for bearer auth")
            elif auth.type == "apiKey" and not auth.api_key:
                raise ValueError("api_key is required for apiKey auth")
            elif auth.type == "basic" and (not auth.username or not auth.password):
                raise ValueError("username and password are required for basic auth")
