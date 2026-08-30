"""FastAPI Observability HTTP Server."""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

MESSAGES_PROCESSED_TOTAL = Counter(
    "telemetry_messages_processed_total",
    "Total count of telemetry messages processed by agent",
)
MESSAGES_SPOOLED_TOTAL = Counter(
    "telemetry_messages_spooled_total",
    "Total count of telemetry messages written to offline spool queue",
)
SPOOL_QUEUE_SIZE = Gauge(
    "telemetry_spool_queue_size",
    "Current count of telemetry messages pending in offline spool queue",
)


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(title="GCP RF Telemetry Collector Agent Observability")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "gcp-rf-telemetry-agent"}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics():
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
