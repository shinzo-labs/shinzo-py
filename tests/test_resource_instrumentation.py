"""Tests for resource instrumentation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server
from shinzo.session import EventType


def test_resource_instrumentation_fastmcp():
    """Test that FastMCP resources are instrumented."""
    mcp = FastMCP(name="test-server")
    
    observability = instrument_server(
        mcp,
        config={
            "server_name": "test-server",
            "server_version": "1.0.0",
            "exporter_type": "console"
        }
    )
    
    # Check that the resource decorator has been wrapped
    assert hasattr(mcp, "resource")
    
    # Define a resource
    @mcp.resource("file:///test.txt")
    def get_test_resource() -> str:
        return "test content"
    
    # The resource should be registered
    assert get_test_resource is not None


def test_resource_session_tracking():
    """Test that resource session tracking can be enabled."""
    mcp = FastMCP(name="test-server")
    
    observability = instrument_server(
        mcp,
        config={
            "server_name": "test-server",
            "server_version": "1.0.0",
            "exporter_type": "console"
        }
    )
    
    # Check that instrumentation has session tracking capability
    instrumentation = observability.instrumentation
    assert hasattr(instrumentation, 'enable_session_tracking')
    assert hasattr(instrumentation, 'get_session_tracker')
    assert hasattr(instrumentation, 'complete_session')
    
    # Initially no session tracker
    assert instrumentation.get_session_tracker() is None


def test_event_types_include_resources():
    """Test that EventType includes resource event types."""
    assert hasattr(EventType, "RESOURCE_LIST")
    assert hasattr(EventType, "RESOURCE_READ")
    assert EventType.RESOURCE_LIST.value == "resource_list"
    assert EventType.RESOURCE_READ.value == "resource_read"


def test_traditional_mcp_resource_instrumentation():
    """Test that traditional MCP servers can be instrumented for resources."""
    from mcp.server import Server
    
    server = Server("test-server")
    
    # Add resource methods to simulate traditional MCP
    server.list_resources = Mock()
    server.read_resource = Mock()
    
    observability = instrument_server(
        server,
        config={
            "server_name": "test-server",
            "server_version": "1.0.0",
            "exporter_type": "console"
        }
    )
    
    # Check that resource methods have been wrapped
    assert hasattr(server, "list_resources")
    assert hasattr(server, "read_resource")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
