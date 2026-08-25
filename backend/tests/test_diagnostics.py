"""
Tests for staged connection diagnostics.

Validates the multi-step connection test pipeline by triggering
failures at specific stages (e.g., wrong port → network failure).
"""

from app.schemas.data_source import ConnectionTestRequest
from app.services import data_source_service


class TestStagedDiagnostics:
    """Tests for the staged connection diagnostics pipeline."""

    def test_wrong_port_fails_at_network_stage(self):
        """Deliberately wrong port should pass config/dns but fail at network."""
        request = ConnectionTestRequest(
            provider="postgresql",
            host="localhost",
            port=9999,
            database_name="pivota",
            username="postgres",
            password="password",
            ssl_enabled=False,
        )
        result = data_source_service.test_connection_unsaved(request)

        assert len(result.steps) == 7
        assert result.steps[0].name == "configuration"
        assert result.steps[0].status == "success"
        assert result.steps[1].name == "dns"
        assert result.steps[1].status == "success"
        assert result.steps[2].name == "network"
        assert result.steps[2].status == "failed"
        assert result.steps[3].name == "tls"
        assert result.steps[3].status == "skipped"
