"""MCP server instrumentation for OpenTelemetry."""

import functools
import time
from typing import Any, Callable, Dict

from opentelemetry.trace import Status, StatusCode

from shinzo.telemetry import TelemetryManager
from shinzo.types import TelemetryConfig, ObservabilityInstance
from shinzo.utils import generate_uuid, get_runtime_info


def instrument_server(server: Any, config: Dict[str, Any] | TelemetryConfig) -> ObservabilityInstance:
    """
    Instrument an MCP server with OpenTelemetry.

    Args:
        server: MCP server instance
        config: Telemetry configuration

    Returns:
        Observability instance for manual instrumentation
    """
    # Convert dict config to TelemetryConfig
    if isinstance(config, dict):
        config = TelemetryConfig(**config)

    telemetry_manager = TelemetryManager(config)
    instrumentation = McpServerInstrumentation(server, telemetry_manager)
    instrumentation.instrument()

    return ObservabilityInstanceImpl(telemetry_manager)


class ObservabilityInstanceImpl:
    """Implementation of the observability instance."""

    def __init__(self, telemetry_manager: TelemetryManager):
        """Initialize with a telemetry manager."""
        self.telemetry_manager = telemetry_manager

    async def start_active_span(
        self,
        name: str,
        attributes: Dict[str, Any],
        fn: Callable
    ) -> Any:
        """Start an active span."""
        return await self.telemetry_manager.start_active_span(name, attributes, fn)

    def get_histogram(self, name: str, description: str, unit: str) -> Callable:
        """Get a histogram metric."""
        return self.telemetry_manager.get_histogram(name, description, unit)

    def get_increment_counter(self, name: str, description: str, unit: str) -> Callable:
        """Get a counter metric."""
        return self.telemetry_manager.get_increment_counter(name, description, unit)

    def process_telemetry_attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process telemetry attributes."""
        return self.telemetry_manager.process_telemetry_attributes(data)

    async def shutdown(self) -> None:
        """Shutdown the observability instance."""
        await self.telemetry_manager.shutdown()


class McpServerInstrumentation:
    """Instrumentation for MCP servers."""

    def __init__(self, server: Any, telemetry_manager: TelemetryManager):
        """
        Initialize the instrumentation.

        Args:
            server: MCP server instance
            telemetry_manager: Telemetry manager
        """
        self.server = server
        self.telemetry_manager = telemetry_manager
        self.is_instrumented = False
        self.client_version_reported = False

    def instrument(self) -> None:
        """Instrument the MCP server."""
        if self.is_instrumented:
            return

        self._instrument_tools()
        self._instrument_prompts()
        self._instrument_resources()
        self._report_client_version()
        # TODO: Add more instrumentation as needed for other MCP operations

        self.is_instrumented = True

    def _report_client_version(self) -> None:
        """Report client version once at initialization."""
        if self.client_version_reported:
            return

        # Try to get client version from the server
        if hasattr(self.server, "get_client_version"):
            client_info = self.server.get_client_version()
            if client_info:
                self.telemetry_manager.report_client_info(client_info)
                self.client_version_reported = True

    def _instrument_tools(self) -> None:
        """Instrument tool calls."""
        if not hasattr(self.server, "call_tool"):
            return

        original_call_tool = self.server.call_tool

        @functools.wraps(original_call_tool)
        def instrumented_call_tool(name: str = None, description: str = None):
            """Instrumented tool decorator."""
            def decorator(func: Callable) -> Callable:
                tool_name = name or func.__name__
                wrapped_func = self._create_instrumented_handler(
                    func,
                    "tools/call",
                    tool_name
                )
                # Call original decorator with the wrapped function
                return original_call_tool(name, description)(wrapped_func)
            return decorator

        self.server.call_tool = instrumented_call_tool

    def _instrument_prompts(self) -> None:
        """Instrument prompt operations."""
        # TODO: Implement prompt instrumentation
        pass

    def _instrument_resources(self) -> None:
        """Instrument resource operations."""
        # TODO: Implement resource instrumentation
        pass

    def _create_instrumented_handler(
        self,
        original_handler: Callable,
        method: str,
        name: str
    ) -> Callable:
        """
        Create an instrumented handler for MCP operations.

        Args:
            original_handler: Original handler function
            method: MCP method name
            name: Operation name (e.g., tool name)

        Returns:
            Instrumented handler
        """
        runtime_info = get_runtime_info()

        base_attributes = {
            "mcp.method.name": method,
            "mcp.tool.name": name
        }

        record_histogram = self.telemetry_manager.get_histogram(
            "mcp.server.operation.duration",
            "MCP request or notification duration",
            "ms"
        )

        increment_counter = self.telemetry_manager.get_increment_counter(
            f"{method} {name}",
            "MCP request or notification count",
            "calls"
        )

        @functools.wraps(original_handler)
        async def instrumented_handler(*args: Any, **kwargs: Any) -> Any:
            """Instrumented handler."""
            # Report client version on first request if not already reported
            if not self.client_version_reported:
                self._report_client_version()

            # Try to get client info for span attributes
            client_info = None
            if hasattr(self.server, "get_client_version"):
                client_info = self.server.get_client_version()

            span_attributes = {
                **base_attributes,
                "mcp.request.id": generate_uuid(),
                "client.address": runtime_info["address"],
            }

            if runtime_info["port"]:
                span_attributes["client.port"] = runtime_info["port"]

            if client_info:
                span_attributes["mcp.client.name"] = client_info.get("name", "unknown")
                if "version" in client_info:
                    span_attributes["mcp.client.version"] = client_info["version"]

            # Extract arguments
            if args:
                params = args[0] if len(args) > 0 else {}
            else:
                params = kwargs

            span_attributes.update(
                self.telemetry_manager.get_argument_attributes(params)
            )

            async def span_fn(span: Any) -> Any:
                increment_counter(1)

                start_time = time.time()
                result = None
                error = None

                try:
                    result = await original_handler(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                except Exception as e:
                    error = e
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", type(e).__name__)

                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to ms

                hist_attributes = dict(base_attributes)
                if error:
                    hist_attributes["error.type"] = type(error).__name__

                record_histogram(duration, hist_attributes)

                if error:
                    raise error

                return result

            return await self.telemetry_manager.start_active_span(
                f"{method} {name}",
                span_attributes,
                span_fn
            )

        return instrumented_handler
