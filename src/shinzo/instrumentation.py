"""MCP server instrumentation for OpenTelemetry."""

import functools
import inspect
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from opentelemetry.trace import Status, StatusCode
from shinzo.session import SessionTracker, SessionEvent, EventType
from shinzo.telemetry import TelemetryManager
from shinzo.types import TelemetryConfig, ObservabilityInstance
from shinzo.utils import generate_uuid, get_runtime_info

S_TO_MS = 1000


def instrument_server(
    server: Any, config: Dict[str, Any] | TelemetryConfig
) -> ObservabilityInstance:
    """
    Instrument an MCP server with OpenTelemetry.

    Args:
        server: MCP server instance
        config: Telemetry configuration

    Returns:
        Observability instance for manual instrumentation
    """
    if isinstance(config, dict):
        config = TelemetryConfig(**config)

    telemetry_manager = TelemetryManager(config)
    instrumentation = McpServerInstrumentation(server, telemetry_manager)
    instrumentation.instrument()

    return ObservabilityInstanceImpl(telemetry_manager, instrumentation)


class ObservabilityInstanceImpl:
    """Implementation of the observability instance."""

    def __init__(
        self, telemetry_manager: TelemetryManager, instrumentation: "McpServerInstrumentation"
    ):
        """Initialize with a telemetry manager and instrumentation."""
        self.telemetry_manager = telemetry_manager
        self.instrumentation = instrumentation

    async def start_active_span(self, name: str, attributes: Dict[str, Any], fn: Callable) -> Any:
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
        self, resource_uuid: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Enable session tracking for debugging and replay.

        Args:
            resource_uuid: UUID of the resource
            metadata: Optional metadata to attach to the session
        """
        if not self.session_tracker:
            self.session_tracker = SessionTracker(self.telemetry_manager.config, resource_uuid)
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
        self._instrument_resources()
        # TODO: Add more instrumentation as needed for other MCP operations
        # self._instrument_prompts()

        self.is_instrumented = True

    def _instrument_tools(self) -> None:
        """Instrument tool calls."""
        if hasattr(self.server, "tool"):
            self._instrument_fastmcp_tools()
        elif hasattr(self.server, "call_tool"):
            self._instrument_traditional_tools()

    def _instrument_fastmcp_tools(self) -> None:
        """Instrument FastMCP tool calls."""
        original_tool = self.server.tool

        def instrumented_tool(*args: Any, **kwargs: Any) -> Callable[[Callable], Callable]:
            """Instrumented FastMCP tool decorator."""

            def decorator(f: Callable) -> Callable:
                tool_name = f.__name__
                wrapped_func = self._create_instrumented_handler(f, "tools/call", tool_name)
                result: Callable = original_tool(*args, **kwargs)(wrapped_func)

                return result

            return decorator

        self.server.tool = instrumented_tool

    def _instrument_traditional_tools(self) -> None:
        """Instrument traditional MCP tool calls."""
        original_call_tool = self.server.call_tool

        @functools.wraps(original_call_tool)
        def instrumented_call_tool(
            *, validate_input: bool = True
        ) -> Callable[[Callable], Callable]:
            """Instrumented tool decorator."""

            def decorator(func: Callable) -> Callable:
                tool_name = func.__name__
                wrapped_func = self._create_instrumented_handler(func, "tools/call", tool_name)
                result: Callable = original_call_tool(validate_input=validate_input)(wrapped_func)
                return result

            return decorator

        self.server.call_tool = instrumented_call_tool

    def _create_instrumented_handler(
        self, original_handler: Callable, method: str, name: str
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
        base_attributes = {"mcp.method.name": method}

        # Add operation-specific attributes
        if method.startswith("resources/"):
            base_attributes["mcp.resource.uri"] = name
        else:
            base_attributes["mcp.tool.name"] = name

        record_histogram = self.telemetry_manager.get_histogram(
            "mcp.server.operation.duration", "MCP request or notification duration", "ms"
        )

        increment_counter = self.telemetry_manager.get_increment_counter(
            f"mcp.server.{method.replace('/', '.').replace(' ', '_')}.{name.replace(' ', '_')}",
            "MCP request or notification count",
            "calls",
        )

        is_async = inspect.iscoroutinefunction(original_handler)

        if is_async:

            @functools.wraps(original_handler)
            async def instrumented_handler(*args: Any, **kwargs: Any) -> Any:
                """Instrumented async handler."""
                return await self._execute_instrumented_call(
                    original_handler,
                    args,
                    kwargs,
                    base_attributes,
                    increment_counter,
                    record_histogram,
                    method,
                    name,
                    True,
                )

        else:

            @functools.wraps(original_handler)
            async def instrumented_handler(*args: Any, **kwargs: Any) -> Any:
                """Instrumented sync handler wrapper."""
                return await self._execute_instrumented_call(
                    original_handler,
                    args,
                    kwargs,
                    base_attributes,
                    increment_counter,
                    record_histogram,
                    method,
                    name,
                    False,
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
        is_async: bool,
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

        if args:
            params = args[0] if len(args) > 0 else {}
        else:
            params = kwargs

        span_attributes.update(self.telemetry_manager.get_argument_attributes(params))

        async def span_fn(span: Any) -> Any:
            increment_counter(1)

            start_time = time.time()
            start_timestamp = datetime.now()
            result = None
            error = None

            # Determine if this is a resource or tool operation
            is_resource_operation = method.startswith("resources/")

            if self.session_tracker and self.session_tracker.is_session_active():
                if is_resource_operation:
                    # For resource operations, determine the event type
                    if method == "resources/list":
                        event_type = EventType.RESOURCE_LIST
                    else:  # resources/read
                        event_type = EventType.RESOURCE_READ

                    self.session_tracker.add_event(
                        SessionEvent(
                            timestamp=start_timestamp,
                            event_type=event_type,
                            resource_uri=name,
                            input_data=(
                                params
                                if self.telemetry_manager.config.enable_argument_collection
                                else None
                            ),
                            metadata={"method": method},
                        )
                    )
                else:
                    # Tool operation
                    self.session_tracker.add_event(
                        SessionEvent(
                            timestamp=start_timestamp,
                            event_type=EventType.TOOL_CALL,
                            tool_name=name,
                            input_data=(
                                params
                                if self.telemetry_manager.config.enable_argument_collection
                                else None
                            ),
                            metadata={"method": method},
                        )
                    )

            try:
                if is_async:
                    result = await original_handler(*args, **kwargs)
                else:
                    result = original_handler(*args, **kwargs)
                span.set_status(Status(StatusCode.OK))

                if self.session_tracker and self.session_tracker.is_session_active():
                    duration_ms = int((time.time() - start_time) * S_TO_MS)

                    if is_resource_operation:
                        # For resource operations, use the same event type for response
                        if method == "resources/list":
                            event_type = EventType.RESOURCE_LIST
                        else:  # resources/read
                            event_type = EventType.RESOURCE_READ

                        self.session_tracker.add_event(
                            SessionEvent(
                                timestamp=datetime.now(),
                                event_type=event_type,
                                resource_uri=name,
                                output_data=(
                                    result
                                    if self.telemetry_manager.config.enable_argument_collection
                                    else None
                                ),
                                duration_ms=duration_ms,
                                metadata={"method": method, "status": "success"},
                            )
                        )
                    else:
                        # Tool operation
                        self.session_tracker.add_event(
                            SessionEvent(
                                timestamp=datetime.now(),
                                event_type=EventType.TOOL_RESPONSE,
                                tool_name=name,
                                output_data=(
                                    result
                                    if self.telemetry_manager.config.enable_argument_collection
                                    else None
                                ),
                                duration_ms=duration_ms,
                                metadata={"method": method},
                            )
                        )
            except Exception as e:
                error = e
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.type", type(e).__name__)

                if self.session_tracker and self.session_tracker.is_session_active():
                    duration_ms = int((time.time() - start_time) * S_TO_MS)
                    self.session_tracker.add_event(
                        SessionEvent(
                            timestamp=datetime.now(),
                            event_type=EventType.ERROR,
                            tool_name=name if not is_resource_operation else None,
                            resource_uri=name if is_resource_operation else None,
                            error_data={
                                "message": str(e),
                                "type": type(e).__name__,
                                "traceback": (
                                    str(e.__traceback__) if hasattr(e, "__traceback__") else None
                                ),
                            },
                            duration_ms=duration_ms,
                            metadata={"method": method},
                        )
                    )

            end_time = time.time()
            duration = (end_time - start_time) * S_TO_MS

            hist_attributes = dict(base_attributes)
            if error:
                hist_attributes["error.type"] = type(error).__name__

            record_histogram(duration, hist_attributes)

            if error:
                raise error

            return result

        return await self.telemetry_manager.start_active_span(
            f"{method} {name}", span_attributes, span_fn
        )

    def _instrument_resources(self) -> None:
        """Instrument resource operations."""
        if hasattr(self.server, "resource"):
            self._instrument_fastmcp_resources()
        elif hasattr(self.server, "list_resources"):
            self._instrument_traditional_resources()

    def _instrument_fastmcp_resources(self) -> None:
        """Instrument FastMCP resource decorators."""
        original_resource = self.server.resource

        def instrumented_resource(*args: Any, **kwargs: Any) -> Callable[[Callable], Callable]:
            """Instrumented FastMCP resource decorator."""

            def decorator(f: Callable) -> Callable:
                resource_uri = kwargs.get("uri", f.__name__)
                wrapped_func = self._create_instrumented_handler(f, "resources/read", resource_uri)
                result: Callable = original_resource(*args, **kwargs)(wrapped_func)

                return result

            return decorator

        self.server.resource = instrumented_resource

    def _instrument_traditional_resources(self) -> None:
        """Instrument traditional MCP resource operations."""
        # Instrument list_resources if it exists
        if hasattr(self.server, "list_resources"):
            original_list_resources = self.server.list_resources

            @functools.wraps(original_list_resources)
            def instrumented_list_resources(
                *, validate_input: bool = True
            ) -> Callable[[Callable], Callable]:
                """Instrumented list_resources decorator."""

                def decorator(func: Callable) -> Callable:
                    wrapped_func = self._create_instrumented_handler(
                        func, "resources/list", "list_resources"
                    )
                    result: Callable = original_list_resources(validate_input=validate_input)(
                        wrapped_func
                    )
                    return result

                return decorator

            self.server.list_resources = instrumented_list_resources

        # Instrument read_resource if it exists
        if hasattr(self.server, "read_resource"):
            original_read_resource = self.server.read_resource

            @functools.wraps(original_read_resource)
            def instrumented_read_resource(
                *, validate_input: bool = True
            ) -> Callable[[Callable], Callable]:
                """Instrumented read_resource decorator."""

                def decorator(func: Callable) -> Callable:
                    wrapped_func = self._create_instrumented_handler(
                        func, "resources/read", "read_resource"
                    )
                    result: Callable = original_read_resource(validate_input=validate_input)(
                        wrapped_func
                    )
                    return result

                return decorator

            self.server.read_resource = instrumented_read_resource
