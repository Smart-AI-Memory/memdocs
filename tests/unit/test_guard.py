"""
Unit tests for guard module (PII/PHI detection and redaction).
"""

from pathlib import Path

from memdocs.guard import Guard, create_guard_from_config
from memdocs.schemas import PHIMode


class TestGuard:
    """Test privacy guard functionality."""

    def test_guard_off_mode(self):
        """Test guard in OFF mode does not redact."""
        guard = Guard(mode=PHIMode.OFF, scrub_types=["email"], audit_path=None)

        text = "Contact me at john@example.com"
        redacted, matches = guard.redact(text, "doc-001")

        assert redacted == text
        assert len(matches) == 0

    def test_detect_email(self):
        """Test email detection."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        text = "Contact john.doe@example.com for info"
        matches = guard.scan(text)

        assert len(matches) == 1
        assert matches[0].type == "email"
        assert "john.doe@example.com" in matches[0].value

    def test_redact_email(self):
        """Test email redaction."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        text = "Contact john@example.com for info"
        redacted, matches = guard.redact(text, "doc-001")

        assert "john@example.com" not in redacted
        assert "[REDACTED:EMAIL]" in redacted
        assert len(matches) == 1

    def test_detect_phone(self):
        """Test phone number detection."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["phone"], audit_path=None)

        text = "Call me at 555-123-4567"
        matches = guard.scan(text)

        assert len(matches) == 1
        assert matches[0].type == "phone"

    def test_detect_ssn(self):
        """Test SSN detection."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["ssn"], audit_path=None)

        text = "SSN: 123-45-6789"
        matches = guard.scan(text)

        assert len(matches) == 1
        assert matches[0].type == "ssn"
        assert "123-45-6789" in matches[0].value

    def test_detect_api_key(self):
        """Test API key detection."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["api_key"], audit_path=None)

        text = "API_KEY: sk-1234567890abcdefghijklmnop"
        matches = guard.scan(text)

        assert len(matches) == 1
        assert matches[0].type == "api_key"

    def test_redact_multiple_types(self):
        """Test redacting multiple PII types."""
        guard = Guard(
            mode=PHIMode.STRICT,
            scrub_types=["email", "phone", "ssn"],
            audit_path=None,
        )

        text = """
        Contact: john@example.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        """
        redacted, matches = guard.redact(text, "doc-001")

        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted
        assert "123-45-6789" not in redacted
        assert len(matches) == 3

    def test_validate_content_clean(self):
        """Test validation of clean content."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        text = "This is clean content with no PII"
        is_valid, errors = guard.validate_content(text)

        assert is_valid
        assert len(errors) == 0

    def test_validate_content_with_pii(self):
        """Test validation fails for content with PII."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        text = "Contact john@example.com"
        is_valid, errors = guard.validate_content(text)

        assert not is_valid
        assert len(errors) > 0

    def test_audit_summary(self):
        """Test audit summary generation."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email", "phone"], audit_path=None)

        text1 = "Email: john@example.com, Phone: 555-123-4567"
        text2 = "Another email: jane@example.com"

        guard.redact(text1, "doc-001")
        guard.redact(text2, "doc-002")

        summary = guard.get_audit_summary()
        assert summary["total_events"] == 2
        assert summary["total_redactions"] == 3
        assert "email" in summary["by_type"]
        assert summary["by_type"]["email"] == 2

    def test_create_guard_from_config(self, tmp_path: Path):
        """Test creating guard from configuration."""
        audit_dir = tmp_path / "audit"
        guard = create_guard_from_config(
            mode=PHIMode.STANDARD,
            scrub_types=["email", "ssn"],
            audit_dir=audit_dir,
        )

        assert guard.mode == PHIMode.STANDARD
        assert "email" in guard.scrub_types
        assert guard.audit_path == audit_dir / "audit.log"

    def test_redaction_context(self):
        """Test that redaction matches include context."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        text = "Please contact support at support@company.com for help"
        matches = guard.scan(text)

        assert len(matches) == 1
        assert len(matches[0].context) > len(matches[0].value)
        assert matches[0].value in matches[0].context

    def test_no_false_positives_common_patterns(self):
        """Test that common non-PII patterns are not flagged."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        # Version numbers, IP-like patterns that aren't IPs, etc.
        text = "Version 1.2.3 released"
        matches = guard.scan(text)

        # Should not detect version as email or other PII
        assert len(matches) == 0

    def test_redact_preserves_format(self):
        """Test that redaction preserves text format."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["email"], audit_path=None)

        text = "Line 1: email1@test.com\nLine 2: email2@test.com"
        redacted, matches = guard.redact(text, "doc-001")

        # Should preserve line breaks
        assert "\n" in redacted
        assert redacted.count("\n") == text.count("\n")

    def test_ipv4_detection(self):
        """Test IPv4 address detection."""
        guard = Guard(mode=PHIMode.STANDARD, scrub_types=["ipv4"], audit_path=None)

        text = "Server at 192.168.1.1"
        matches = guard.scan(text)

        assert len(matches) == 1
        assert matches[0].type == "ipv4"
        assert matches[0].value == "192.168.1.1"

    def test_audit_log_written(self, tmp_path: Path):
        """Test that audit log is written to file."""
        audit_path = tmp_path / "audit.log"
        guard = Guard(
            mode=PHIMode.STANDARD,
            scrub_types=["email"],
            audit_path=audit_path,
        )

        text = "Contact john@example.com"
        guard.redact(text, "doc-001")

        assert audit_path.exists()
        content = audit_path.read_text()
        assert "redaction_applied" in content
        assert "email" in content
