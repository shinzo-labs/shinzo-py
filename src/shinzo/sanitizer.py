"""PII sanitization for telemetry data."""

import re
from typing import Any, Dict, List, Pattern


class PIISanitizer:
    """Sanitizer for personally identifiable information in telemetry data."""

    DEFAULT_PII_PATTERNS: List[Pattern] = [
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
        re.compile(r"\b\d{16}\b"),  # Credit card
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # IP address
    ]

    def __init__(self, patterns: List[Pattern] | None = None, redact_value: str = "[REDACTED]"):
        """
        Initialize the PII sanitizer.

        Args:
            patterns: Custom regex patterns to match PII
            redact_value: Value to replace PII with
        """
        self.patterns = patterns or self.DEFAULT_PII_PATTERNS
        self.redact_value = redact_value

    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize PII from the data.

        Args:
            data: Dictionary containing telemetry data

        Returns:
            Sanitized dictionary with PII removed
        """
        if not isinstance(data, dict):
            return data

        sanitized: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        self._sanitize_string(item)
                        if isinstance(item, str)
                        else self.sanitize(item) if isinstance(item, dict) else item
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize a string value.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        result = value
        for pattern in self.patterns:
            result = pattern.sub(self.redact_value, result)
        return result

    def redact_pii_attributes(self) -> Any:
        """Return a resource detector that redacts PII from resource attributes."""
        # This would integrate with OpenTelemetry resource detection
        # For now, return a placeholder
        return None
