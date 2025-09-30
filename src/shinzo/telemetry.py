"""Telemetry management for MCP servers."""

import base64
import time
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from shinzo.types import TelemetryConfig
from shinzo.config import ConfigValidator, DEFAULT_CONFIG
from shinzo.sanitizer import PIISanitizer
from shinzo.utils import generate_uuid


class TelemetryManager:
    """Manager for OpenTelemetry tracing and metrics."""

    def __init__(self, config: TelemetryConfig):
        """
        Initialize the telemetry manager.

        Args:
            config: Telemetry configuration
        """
        ConfigValidator.validate(config)

        # Merge with defaults
        self.config = config
        for key, value in DEFAULT_CONFIG.items():
            if not hasattr(config, key) or getattr(config, key) is None:
                setattr(self.config, key, value)

        self.session_id = generate_uuid()
        self.session_start = time.time()
        self.is_initialized = False

        # Initialize PII sanitizer if enabled
        self.pii_sanitizer: Optional[PIISanitizer] = None
        if self.config.enable_pii_sanitization:
            self.pii_sanitizer = config.pii_sanitizer or PIISanitizer()

        # Create resource
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: self.config.server_name,
            ResourceAttributes.SERVICE_VERSION: self.config.server_version,
            "mcp.session.id": self.session_id,
        })

        # Initialize tracing
        if self.config.enable_tracing:
            self._init_tracing(resource)

        # Initialize metrics
        if self.config.enable_metrics:
            self._init_metrics(resource)

        self.is_initialized = True

    def _get_otlp_headers(self) -> Dict[str, str]:
        """Get headers for OTLP exporter."""
        headers = {}
        if self.config.exporter_auth:
            auth = self.config.exporter_auth
            if auth.type == "bearer":
                headers["Authorization"] = f"Bearer {auth.token}"
            elif auth.type == "apiKey":
                headers["X-API-Key"] = auth.api_key
            elif auth.type == "basic":
                credentials = f"{auth.username}:{auth.password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        return headers

    def _init_tracing(self, resource: Resource) -> None:
        """Initialize tracing."""
        if self.config.exporter_type == "console":
            exporter = ConsoleSpanExporter()
        else:
            headers = self._get_otlp_headers()
            endpoint = self.config.exporter_endpoint
            if not endpoint.endswith("/"):
                endpoint += "/"
            endpoint += "traces"
            exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)

        # Set up sampler
        sampler = TraceIdRatioBased(self.config.sampling_rate)

        # Create tracer provider
        provider = TracerProvider(resource=resource, sampler=sampler)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        self.tracer = trace.get_tracer(
            self.config.server_name,
            self.config.server_version
        )

    def _init_metrics(self, resource: Resource) -> None:
        """Initialize metrics."""
        if self.config.exporter_type == "console":
            exporter = ConsoleMetricExporter()
        else:
            headers = self._get_otlp_headers()
            endpoint = self.config.exporter_endpoint
            if not endpoint.endswith("/"):
                endpoint += "/"
            endpoint += "metrics"
            exporter = OTLPMetricExporter(endpoint=endpoint, headers=headers)

        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=self.config.metric_export_interval_ms,
            export_timeout_millis=self.config.batch_timeout_ms,
        )

        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)

        self.meter = metrics.get_meter(
            self.config.server_name,
            self.config.server_version
        )

    async def start_active_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        fn: Callable
    ) -> Any:
        """
        Start an active span and execute a function within it.

        Args:
            name: Span name
            attributes: Span attributes
            fn: Function to execute within the span

        Returns:
            Result of the function
        """
        if not self.is_initialized:
            raise RuntimeError("Telemetry not initialized")

        processed_attributes = self._process_telemetry_attributes_with_session_id(attributes)

        with self.tracer.start_as_current_span(name, attributes=processed_attributes) as span:
            return await fn(span)

    def get_histogram(self, name: str, description: str, unit: str) -> Callable:
        """
        Get a histogram metric.

        Args:
            name: Metric name
            description: Metric description
            unit: Metric unit

        Returns:
            Function to record histogram values
        """
        if not self.is_initialized:
            raise RuntimeError("Telemetry not initialized")

        histogram = self.meter.create_histogram(
            name=name,
            description=description,
            unit=unit
        )

        def record(value: float, attributes: Optional[Dict[str, Any]] = None) -> None:
            processed_attributes = self._process_telemetry_attributes_with_session_id(
                attributes or {}
            )
            histogram.record(value, attributes=processed_attributes)

        return record

    def get_increment_counter(self, name: str, description: str, unit: str) -> Callable:
        """
        Get a counter metric.

        Args:
            name: Metric name
            description: Metric description
            unit: Metric unit

        Returns:
            Function to increment the counter
        """
        if not self.is_initialized:
            raise RuntimeError("Telemetry not initialized")

        counter = self.meter.create_counter(
            name=name,
            description=description,
            unit=unit
        )

        def increment(value: int, attributes: Optional[Dict[str, Any]] = None) -> None:
            processed_attributes = self._process_telemetry_attributes_with_session_id(
                attributes or {}
            )
            counter.add(value, attributes=processed_attributes)

        return increment

    def get_argument_attributes(
        self,
        params: Any,
        prefix: str = "mcp.request.argument"
    ) -> Dict[str, Any]:
        """
        Extract attributes from parameters.

        Args:
            params: Parameters to extract attributes from
            prefix: Prefix for attribute keys

        Returns:
            Dictionary of attributes
        """
        if not self.config.enable_argument_collection:
            return {}

        attributes: Dict[str, Any] = {}

        def flatten(obj: Any, path: str) -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    attr_key = f"{path}.{key}"
                    if isinstance(value, dict):
                        flatten(value, attr_key)
                    else:
                        attributes[attr_key] = value

        if isinstance(params, dict):
            flatten(params, prefix)

        return attributes

    def report_client_info(self, client_info: Dict[str, Any]) -> None:
        """
        Report MCP client information as a metric.

        Args:
            client_info: Dictionary with 'name' and optional 'version' keys
        """
        if not self.config.enable_metrics:
            return

        increment_counter = self.get_increment_counter(
            "mcp.client.connections",
            "Count of MCP client connections by client type and version",
            "connections"
        )

        increment_counter(1, {
            "mcp.client.name": client_info.get("name", "unknown"),
            "mcp.client.version": client_info.get("version", "unknown")
        })

    def _record_session_duration(self) -> None:
        """Record the session duration metric."""
        if self.config.enable_metrics:
            record_histogram = self.get_histogram(
                "mcp.server.session.duration",
                "MCP server session duration",
                "s"
            )
            duration = time.time() - self.session_start
            record_histogram(duration, {"mcp.session.id": self.session_id})

    def _process_telemetry_attributes_with_session_id(
        self,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process telemetry attributes and add session ID."""
        return self.process_telemetry_attributes({
            "mcp.session.id": self.session_id,
            **(data or {})
        })

    def process_telemetry_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process telemetry attributes through data processors and sanitizers.

        Args:
            data: Attributes to process

        Returns:
            Processed attributes
        """
        processed_data = dict(data)

        # Apply custom data processors
        if self.config.data_processors:
            for processor in self.config.data_processors:
                processed_data = processor(processed_data)

        # Apply PII sanitization
        if self.pii_sanitizer:
            processed_data = self.pii_sanitizer.sanitize(processed_data)

        return processed_data

    async def shutdown(self) -> None:
        """Shutdown the telemetry manager."""
        self._record_session_duration()

        # Shutdown tracer provider
        if self.config.enable_tracing:
            tracer_provider = trace.get_tracer_provider()
            if hasattr(tracer_provider, "shutdown"):
                tracer_provider.shutdown()

        # Shutdown meter provider
        if self.config.enable_metrics:
            meter_provider = metrics.get_meter_provider()
            if hasattr(meter_provider, "shutdown"):
                meter_provider.shutdown()
