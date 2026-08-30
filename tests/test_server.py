"""Unit tests for FastAPI observability health and metrics server."""

import pytest
from fastapi.testclient import TestClient


def test_healthz_and_metrics_endpoints():
    from agent.server import create_app

    app = create_app()
    client = TestClient(app)

    response_health = client.get("/healthz")
    assert response_health.status_code == 200
    assert response_health.json() == {"status": "ok", "service": "gcp-rf-telemetry-agent"}

    response_metrics = client.get("/metrics")
    assert response_metrics.status_code == 200
    assert "telemetry_messages_processed_total" in response_metrics.text
