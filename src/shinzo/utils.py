"""Utility functions for Shinzo."""

import socket
import uuid
from typing import Dict, Tuple


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def get_runtime_info() -> Dict[str, any]:
    """Get runtime information including address and port."""
    try:
        hostname = socket.gethostname()
        address = socket.gethostbyname(hostname)
    except Exception:
        address = "unknown"

    return {
        "address": address,
        "port": None  # Port may not be applicable for stdio MCP servers
    }
