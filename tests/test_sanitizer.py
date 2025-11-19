"""Tests for PII sanitization."""

from shinzo.sanitizer import PIISanitizer


def test_sanitize_email():
    """Test that email addresses are sanitized."""
    sanitizer = PIISanitizer()
    data = {"email": "user@example.com", "message": "Contact me at admin@test.org"}
    result = sanitizer.sanitize(data)
    assert result["email"] == "[REDACTED]"
    assert "[REDACTED]" in result["message"]
    assert "admin@test.org" not in result["message"]


def test_sanitize_nested_data():
    """Test that nested data is sanitized."""
    sanitizer = PIISanitizer()
    data = {"user": {"email": "user@example.com", "profile": {"contact": "admin@test.org"}}}
    result = sanitizer.sanitize(data)
    assert result["user"]["email"] == "[REDACTED]"
    assert result["user"]["profile"]["contact"] == "[REDACTED]"


def test_sanitize_list():
    """Test that lists are sanitized."""
    sanitizer = PIISanitizer()
    data = {"emails": ["user1@example.com", "user2@example.com"]}
    result = sanitizer.sanitize(data)
    assert result["emails"] == ["[REDACTED]", "[REDACTED]"]


def test_non_pii_data_unchanged():
    """Test that non-PII data is unchanged."""
    sanitizer = PIISanitizer()
    data = {"name": "John Doe", "age": 30, "active": True}
    result = sanitizer.sanitize(data)
    assert result == data
