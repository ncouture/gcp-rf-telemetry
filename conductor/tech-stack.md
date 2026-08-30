# Technology Stack: GCP RF Telemetry Collector Agent

## Language & Core Runtime
- **Language:** Python 3.11+
- **Concurrency & Async:** `asyncio` for non-blocking I/O, concurrent streaming, and timer schedules

## Data Serialization & Messaging
- **Serialization:** Protocol Buffers (`protobuf`) for compact binary telemetry schema
- **GCP Transport:** `google-cloud-pubsub` (gRPC / HTTP REST client for Cloud Pub/Sub)

## Storage & Spooling
- **Offline Spooling Database:** SQLite 3 (`aiosqlite` / `sqlite3`) for persistent local disk queuing during GCP network outages

## Observability & Server Framework
- **HTTP Server / Health Check / Metrics:** FastAPI / Uvicorn for `/healthz` and `/metrics`
- **Prometheus Metrics:** `prometheus_client` for exposing collector throughput and queue metrics
- **Logging:** `python-json-logger` formatted for GCP Cloud Logging schema

## Containerization & CI/CD
- **Containerization:** Docker multi-stage build (Alpine/Slim Python base image)
- **CI/CD Pipeline:** GitHub Actions (`.github/workflows/deploy.yml`) for Docker build, Google Artifact Registry push, and GCP Cloud Run deployment

## Testing Framework
- **Test Runner:** `pytest`, `pytest-asyncio`
- **Mocking & Quality:** `unittest.mock` for GCP Pub/Sub client mocking, `ruff`/`black` for linting & formatting
