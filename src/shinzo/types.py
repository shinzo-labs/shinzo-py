"""Type definitions for Shinzo."""

from typing import Any, Callable, Dict, Literal, Optional, Protocol
from pydantic import BaseModel


class AuthConfig(BaseModel):
    """Authentication configuration for OTLP exporter."""

    type: Literal["bearer", "apiKey", "basic"]
    token: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class TelemetryConfig(BaseModel):
    """Configuration for telemetry collection and export."""

    server_name: str
    server_version: str
    exporter_endpoint: Optional[str] = "http://localhost:4318/v1/otlp"
    exporter_auth: Optional[AuthConfig] = None
    sampling_rate: Optional[float] = 1.0
    metric_export_interval_ms: Optional[int] = 60000
    enable_pii_sanitization: Optional[bool] = False
    enable_argument_collection: Optional[bool] = True
    data_processors: Optional[list[Callable[[Dict[str, Any]], Dict[str, Any]]]] = None
    exporter_type: Optional[Literal["otlp-http", "console"]] = "otlp-http"
    enable_metrics: Optional[bool] = True
    enable_tracing: Optional[bool] = True
    batch_timeout_ms: Optional[int] = 30000
    pii_sanitizer: Optional[Any] = None


class ObservabilityInstance(Protocol):
    """Protocol for observability instance."""

    async def start_active_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        fn: Callable
    ) -> Any:
        """Start an active span."""
        ...

    def get_histogram(self, name: str, description: str, unit: str) -> Callable:
        """Get a histogram metric."""
        ...

    def get_increment_counter(self, name: str, description: str, unit: str) -> Callable:
        """Get a counter metric."""
        ...

    def process_telemetry_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process telemetry attributes."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the observability instance."""
        ...
