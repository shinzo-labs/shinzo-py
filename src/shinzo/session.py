"""Session tracking for MCP server interactions."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from shinzo.types import TelemetryConfig
from shinzo.utils import generate_uuid


class EventType(str, Enum):
    """Types of session events."""

    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    ERROR = "error"
    USER_INPUT = "user_input"
    SYSTEM_MESSAGE = "system_message"


@dataclass
class SessionEvent:
    """Represents a single event in a session."""

    timestamp: datetime
    event_type: EventType
    tool_name: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionTracker:
    """Tracks session events and sends them to the backend."""

    def __init__(self, config: TelemetryConfig, resource_uuid: str):
        """
        Initialize the session tracker.

        Args:
            config: Telemetry configuration
            resource_uuid: UUID of the resource this session belongs to
        """
        self.config = config
        self.session_id = generate_uuid()
        self.session_uuid: Optional[str] = None
        self.resource_uuid = resource_uuid
        self.start_time = datetime.now()
        self.event_queue: List[SessionEvent] = []
        self.is_active = False
        self.flush_task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Start the session tracking.

        Args:
            metadata: Optional metadata to attach to the session
        """
        if self.is_active:
            return

        try:
            response = await self._send_to_backend(
                "/sessions/create",
                {
                    "session_id": self.session_id,
                    "resource_uuid": self.resource_uuid,
                    "start_time": self.start_time.isoformat(),
                    "metadata": metadata,
                },
            )

            if response and "session_uuid" in response:
                self.session_uuid = response["session_uuid"]
                self.is_active = True

                # Start periodic flush task
                self.flush_task = asyncio.create_task(self._periodic_flush())
        except Exception as e:
            print(f"Failed to start session tracking: {e}")

    def add_event(self, event: SessionEvent) -> None:
        """
        Add an event to the session.

        Args:
            event: The event to add
        """
        if not self.is_active or not self.session_uuid:
            return

        self.event_queue.append(event)

        # If queue gets large, flush immediately
        if len(self.event_queue) >= 10:
            asyncio.create_task(self.flush_events())

    async def flush_events(self) -> None:
        """Flush queued events to the backend."""
        if not self.is_active or not self.session_uuid or not self.event_queue:
            return

        events_to_send = self.event_queue.copy()
        self.event_queue.clear()

        try:
            for event in events_to_send:
                await self._send_to_backend(
                    "/sessions/add_event",
                    {
                        "session_uuid": self.session_uuid,
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type.value,
                        "tool_name": event.tool_name,
                        "input_data": event.input_data,
                        "output_data": event.output_data,
                        "error_data": event.error_data,
                        "duration_ms": event.duration_ms,
                        "metadata": event.metadata,
                    },
                )
        except Exception as e:
            print(f"Failed to flush session events: {e}")
            # Re-add events to queue if flush failed
            self.event_queue = events_to_send + self.event_queue

    async def complete(self) -> None:
        """Complete the session."""
        if not self.is_active or not self.session_uuid:
            return

        # Flush any remaining events
        await self.flush_events()

        # Cancel periodic flush task
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass

        try:
            await self._send_to_backend(
                "/sessions/complete",
                {"session_uuid": self.session_uuid, "end_time": datetime.now().isoformat()},
            )

            self.is_active = False
        except Exception as e:
            print(f"Failed to complete session: {e}")
        finally:
            if self._client:
                await self._client.aclose()
                self._client = None

    async def _periodic_flush(self) -> None:
        """Periodically flush events to the backend."""
        try:
            while self.is_active:
                await asyncio.sleep(5)  # Flush every 5 seconds
                await self.flush_events()
        except asyncio.CancelledError:
            pass

    async def _send_to_backend(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send data to the backend.

        Args:
            endpoint: API endpoint path
            data: Data to send

        Returns:
            Response data if successful
        """
        if not self.config.exporter_endpoint:
            raise ValueError("Exporter endpoint not configured")

        # Initialize client if needed
        if not self._client:
            self._client = httpx.AsyncClient(timeout=30.0)

        # Build URL
        base_url = self.config.exporter_endpoint.replace("/v1/traces", "")
        url = f"{base_url}{endpoint}"

        # Build headers
        headers = {"Content-Type": "application/json"}

        # Add authentication
        if self.config.exporter_auth:
            auth = self.config.exporter_auth
            if auth.type == "bearer":
                if not auth.token:
                    raise ValueError("Bearer token is required for bearer authentication")
                headers["Authorization"] = f"Bearer {auth.token}"
            elif auth.type == "apiKey":
                if not auth.api_key:
                    raise ValueError("API key is required for apiKey authentication")
                headers["X-API-Key"] = auth.api_key
            elif auth.type == "basic":
                if not auth.username or not auth.password:
                    raise ValueError("Username and password are required for basic authentication")
                import base64

                credentials = base64.b64encode(f"{auth.username}:{auth.password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

        # Send request
        response = await self._client.post(url, json=data, headers=headers)
        response.raise_for_status()

        result = response.json()
        return result if isinstance(result, dict) else None

    def get_session_id(self) -> str:
        """Get the session ID."""
        return self.session_id

    def is_session_active(self) -> bool:
        """Check if the session is active."""
        return self.is_active
