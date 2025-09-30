"""Shinzo - Complete Observability for MCP servers."""

from shinzo.instrumentation import instrument_server
from shinzo.telemetry import TelemetryManager
from shinzo.sanitizer import PIISanitizer
from shinzo.config import ConfigValidator, TelemetryConfig
from shinzo.types import ObservabilityInstance, AuthConfig

__version__ = "1.0.0"

__all__ = [
    "instrument_server",
    "TelemetryManager",
    "PIISanitizer",
    "ConfigValidator",
    "TelemetryConfig",
    "ObservabilityInstance",
    "AuthConfig",
]
