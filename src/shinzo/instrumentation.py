"""MCP server instrumentation for OpenTelemetry."""

import functools
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from opentelemetry.trace import Status, StatusCode

from shinzo.session import SessionTracker, SessionEvent, EventType
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

    return ObservabilityInstanceImpl(telemetry_manager, instrumentation)


class ObservabilityInstanceImpl:
    """Implementation of the observability instance."""

    def __init__(self, telemetry_manager: TelemetryManager, instrumentation: 'McpServerInstrumentation'):
        """Initialize with a telemetry manager and instrumentation."""
        self.telemetry_manager = telemetry_manager
        self.instrumentation = instrumentation

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
        self.session_tracker: Optional[SessionTracker] = None

    async def enable_session_tracking(
        self,
        resource_uuid: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Enable session tracking for debugging and replay.

        Args:
            resource_uuid: UUID of the resource
            metadata: Optional metadata to attach to the session
        """
        if not self.session_tracker:
            self.session_tracker = SessionTracker(
                self.telemetry_manager.config,
                resource_uuid
            )
            await self.session_tracker.start(metadata)

    def get_session_tracker(self) -> Optional[SessionTracker]:
        """Get the session tracker instance."""
        return self.session_tracker

    async def complete_session(self) -> None:
        """Complete the current session."""
        if self.session_tracker:
            await self.session_tracker.complete()
            self.session_tracker = None

    def instrument(self) -> None:
        """Instrument the MCP server."""
        if self.is_instrumented:
            return

        self._instrument_tools()
        self._instrument_prompts()
        self._instrument_resources()
        # TODO: Add more instrumentation as needed for other MCP operations

        self.is_instrumented = True

    def _instrument_tools(self) -> None:
        """Instrument tool calls."""
        # Handle FastMCP servers
        if hasattr(self.server, "tool"):
            self._instrument_fastmcp_tools()
        # Handle traditional MCP servers
        elif hasattr(self.server, "call_tool"):
            self._instrument_traditional_tools()

    def _instrument_fastmcp_tools(self) -> None:
        """Instrument FastMCP tool calls."""
        original_tool = self.server.tool

        def instrumented_tool():
            """Instrumented FastMCP tool decorator."""
            def decorator(f: Callable) -> Callable:
                tool_name = f.__name__
                wrapped_func = self._create_instrumented_handler(
                    f,
                    "tools/call",
                    tool_name
                )
                # Call original decorator with the wrapped function
                return original_tool()(wrapped_func)
            
            return decorator

        self.server.tool = instrumented_tool

    def _instrument_traditional_tools(self) -> None:
        """Instrument traditional MCP tool calls."""
        original_call_tool = self.server.call_tool

        @functools.wraps(original_call_tool)
        def instrumented_call_tool(*, validate_input: bool = True):
            """Instrumented tool decorator."""
            def decorator(func: Callable) -> Callable:
                tool_name = func.__name__
                wrapped_func = self._create_instrumented_handler(
                    func,
                    "tools/call",
                    tool_name
                )
                # Call original decorator with the wrapped function
                return original_call_tool(validate_input=validate_input)(wrapped_func)
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
            f"mcp.server.{method.replace('/', '.').replace(' ', '_')}.{name.replace(' ', '_')}",
            "MCP request or notification count",
            "calls"
        )

        # Check if the original handler is async or sync
        import inspect
        is_async = inspect.iscoroutinefunction(original_handler)

        if is_async:
            @functools.wraps(original_handler)
            async def instrumented_handler(*args: Any, **kwargs: Any) -> Any:
                """Instrumented async handler."""
                return await self._execute_instrumented_call(
                    original_handler, args, kwargs, base_attributes, 
                    increment_counter, record_histogram, method, name, True
                )
        else:
            @functools.wraps(original_handler)
            async def instrumented_handler(*args: Any, **kwargs: Any) -> Any:
                """Instrumented sync handler wrapper."""
                return await self._execute_instrumented_call(
                    original_handler, args, kwargs, base_attributes,
                    increment_counter, record_histogram, method, name, False
                )

        return instrumented_handler

    async def _execute_instrumented_call(
        self,
        original_handler: Callable,
        args: tuple,
        kwargs: dict,
        base_attributes: Dict[str, Any],
        increment_counter: Callable,
        record_histogram: Callable,
        method: str,
        name: str,
        is_async: bool
    ) -> Any:
        """Execute an instrumented call with telemetry."""
        runtime_info = get_runtime_info()
        
        span_attributes = {
            **base_attributes,
            "mcp.request.id": generate_uuid(),
            "client.address": runtime_info["address"],
        }

        if runtime_info["port"]:
            span_attributes["client.port"] = runtime_info["port"]

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
            start_timestamp = datetime.now()
            result = None
            error = None

            # Track tool call event if session tracking is enabled
            if self.session_tracker and self.session_tracker.is_session_active():
                self.session_tracker.add_event(
                    SessionEvent(
                        timestamp=start_timestamp,
                        event_type=EventType.TOOL_CALL,
                        tool_name=name,
                        input_data=params if self.telemetry_manager.config.enable_argument_collection else None,
                        metadata={"method": method}
                    )
                )

            try:
                if is_async:
                    result = await original_handler(*args, **kwargs)
                else:
                    result = original_handler(*args, **kwargs)
                span.set_status(Status(StatusCode.OK))

                # Track successful tool response
                if self.session_tracker and self.session_tracker.is_session_active():
                    duration_ms = int((time.time() - start_time) * 1000)
                    self.session_tracker.add_event(
                        SessionEvent(
                            timestamp=datetime.now(),
                            event_type=EventType.TOOL_RESPONSE,
                            tool_name=name,
                            output_data=result if self.telemetry_manager.config.enable_argument_collection else None,
                            duration_ms=duration_ms,
                            metadata={"method": method}
                        )
                    )
            except Exception as e:
                error = e
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", type(e).__name__)

                # Track error event
                if self.session_tracker and self.session_tracker.is_session_active():
                    duration_ms = int((time.time() - start_time) * 1000)
                    self.session_tracker.add_event(
                        SessionEvent(
                            timestamp=datetime.now(),
                            event_type=EventType.ERROR,
                            tool_name=name,
                            error_data={
                                "message": str(e),
                                "type": type(e).__name__,
                                "traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
                            },
                            duration_ms=duration_ms,
                            metadata={"method": method}
                        )
                    )

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
