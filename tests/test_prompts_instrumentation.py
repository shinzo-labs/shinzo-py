"""Tests for prompt instrumentation."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from shinzo.instrumentation import McpServerInstrumentation
from shinzo.session import EventType, SessionEvent
from shinzo.types import TelemetryConfig


class MockFastMCPServer:
    """Mock FastMCP server with prompt decorator."""

    def __init__(self) -> None:
        self.prompt_registry = {}

    def prompt(self, name: str = None) -> None:
        def decorator(func):
            prompt_name = name or func.__name__
            self.prompt_registry[prompt_name] = func
            return func
        return decorator


class MockTraditionalServer:
    """Mock traditional MCP server."""

    async def get_prompt(self, name: str, arguments: dict = None) -> str:
        if name == "error_prompt":
            raise ValueError("Prompt error")
        return f"Result for {name}"

    async def list_prompts(self, cursor: str = None) -> list:
        return ["p1", "p2"]


def _get_telemetry_manager() -> MagicMock:
    """Get a mock telemetry manager."""
    manager = MagicMock()
    manager.config = TelemetryConfig(
        server_name="test",
        server_version="1.0.0",
        enable_argument_collection=True
    )
    
    async def mock_start_span(name, attributes, fn):
        span = MagicMock()
        return await fn(span)
    
    manager.start_active_span = AsyncMock(side_effect=mock_start_span)
    manager.get_increment_counter.return_value = MagicMock()
    manager.get_histogram.return_value = MagicMock()
    manager.get_argument_attributes.return_value = {}
    return manager


@pytest.mark.asyncio
async def test_fastmcp_prompt_instrumentation() -> None:
    """Test instrumentation of FastMCP style prompts."""
    # Setup
    server = MockFastMCPServer()
    telemetry_manager = _get_telemetry_manager()
    session_tracker = MagicMock()
    session_tracker.is_session_active.return_value = True

    instrumentation = McpServerInstrumentation(server, telemetry_manager)
    instrumentation.session_tracker = session_tracker
    
    # Instrument
    instrumentation._instrument_prompts()
    
    # Define and call prompt
    @server.prompt(name="custom_prompt")
    async def my_prompt(foo: str):
        return f"bar-{foo}"
    
    result = await my_prompt(foo="baz")
    
    # Verify
    assert result == "bar-baz"
    
    # Verify Telemetry
    telemetry_manager.start_active_span.assert_called_once()
    args, _ = telemetry_manager.start_active_span.call_args
    span_name, attributes, _ = args
    
    assert span_name == "prompts/get custom_prompt"
    assert attributes["mcp.method.name"] == "prompts/get"
    assert attributes["mcp.prompt.name"] == "custom_prompt"
    
    # Verify Event
    events = [call[0][0] for call in session_tracker.add_event.call_args_list]
    prompt_event = next((e for e in events if e.event_type == EventType.PROMPT_GET), None)
    
    assert prompt_event is not None
    assert prompt_event.tool_name == "custom_prompt"
    assert prompt_event.input_data == {"foo": "baz"}


@pytest.mark.asyncio
async def test_traditional_get_prompt() -> None:
    """Test instrumentation of traditional get_prompt."""
    # Setup
    server = MockTraditionalServer()
    telemetry_manager = _get_telemetry_manager()
    session_tracker = MagicMock()
    session_tracker.is_session_active.return_value = True

    instrumentation = McpServerInstrumentation(server, telemetry_manager)
    instrumentation.session_tracker = session_tracker
    
    # Instrument
    instrumentation._instrument_prompts()
    
    # Execute
    result = await server.get_prompt("test-prompt", arguments={"key": "val"})
    assert result == "Result for test-prompt"
    
    # Verify Telemetry
    args, _ = telemetry_manager.start_active_span.call_args
    _, attributes, _ = args
    assert attributes["mcp.prompt.name"] == "test-prompt"
    
    # Verify Event
    events = [call[0][0] for call in session_tracker.add_event.call_args_list]
    event = next((e for e in events if e.event_type == EventType.PROMPT_GET), None)
    assert event.tool_name == "test-prompt"


@pytest.mark.asyncio
async def test_traditional_list_prompts() -> None:
    """Test instrumentation of traditional list_prompts."""
    # Setup
    server = MockTraditionalServer()
    telemetry_manager = _get_telemetry_manager()
    session_tracker = MagicMock()
    session_tracker.is_session_active.return_value = True

    instrumentation = McpServerInstrumentation(server, telemetry_manager)
    instrumentation.session_tracker = session_tracker
    
    # Instrument
    instrumentation._instrument_prompts()
    
    # Execute
    result = await server.list_prompts()
    assert result == ["p1", "p2"]
    
    # Verify Telemetry
    args, _ = telemetry_manager.start_active_span.call_args
    span_name, attributes, _ = args
    assert span_name == "prompts/list"
    
    # Verify Event
    events = [call[0][0] for call in session_tracker.add_event.call_args_list]
    event = next((e for e in events if e.event_type == EventType.PROMPT_LIST), None)
    assert event is not None


@pytest.mark.asyncio
async def test_prompt_error_handling() -> None:
    """Test that errors in prompts are captured."""
    # Setup
    server = MockTraditionalServer()
    telemetry_manager = _get_telemetry_manager()
    session_tracker = MagicMock()
    session_tracker.is_session_active.return_value = True

    instrumentation = McpServerInstrumentation(server, telemetry_manager)
    instrumentation.session_tracker = session_tracker
    
    # Instrument
    instrumentation._instrument_prompts()
    
    # Execute
    with pytest.raises(ValueError, match="Prompt error"):
        await server.get_prompt("error_prompt")
        
    # Verify Error Event
    events = [call[0][0] for call in session_tracker.add_event.call_args_list]
    error_event = next((e for e in events if e.event_type == EventType.ERROR), None)
    
    assert error_event is not None
    assert error_event.tool_name == "error_prompt"
    assert error_event.error_data["message"] == "Prompt error"
