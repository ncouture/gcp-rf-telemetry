# Track Specification: MVP Implementation

## Overview
The **MVP Implementation** track establishes the core foundation for the **GCP RF Telemetry Collector Agent**. This includes the Protocol Buffers (`telemetry.proto`) schema definition supporting spectral sweep RF telemetry data, a static CSV mock data reader/generator, an offline SQLite buffer spooler, a GCP Pub/Sub publisher with local emulator/mock fallback, a FastAPI `/healthz` and `/metrics` server, Docker container packaging, and GitHub Actions CI/CD workflows for GCP Cloud Run deployment.

## Functional Requirements

### 1. Protobuf Telemetry Schema & Codegen (`telemetry.proto`)
- Define `RfTelemetryMessage` containing:
  - Timestamp (ISO string / Unix epoch)
  - Frequency bounds (`hz_low`, `hz_high`, `hz_bin_width`)
  - Sample count (`num_samples`)
  - Spectral power density values (`db_bins`: repeated float array for power spectrum measurements across frequency bins)
  - Device/Sensor ID and metadata
- Python Protobuf compilation (`protoc`) integration.

### 2. Mock CSV Data Reader & Generator
- Parse CSV files containing spectral telemetry records with headers: `date, time, hz_low, hz_high, hz_bin_width, num_samples, dB...`
- Transform CSV rows into strongly typed `RfTelemetryMessage` Protobuf payloads.
- Stream records at configurable sample intervals with looping support for local testing.

### 3. SQLite Offline Buffer & Spooler
- Persistent local SQLite queue database (`telemetry_spool.db`) to buffer telemetry messages when GCP Pub/Sub is unreachable or offline.
- Automatic queue drain and re-transmission upon connection restoration.

### 4. GCP Pub/Sub Publisher Client
- Async publisher module for GCP Cloud Pub/Sub using `google-cloud-pubsub`.
- Support for `PUBSUB_EMULATOR_HOST` and mock publisher mode for local offline execution without live GCP credentials.
- Configurable topic ID (`GCP_PROJECT_ID`, `PUBSUB_TOPIC_ID`).

### 5. HTTP Observability & Health Server
- Lightweight FastAPI / Uvicorn HTTP server exposing:
  - `GET /healthz`: Health check probe endpoint.
  - `GET /metrics`: Prometheus metric scraping endpoint tracking processed messages, spool count, and error rates.

### 6. Containerization & CI/CD Pipeline
- Multi-stage Dockerfile for containerized edge / Cloud Run runtime.
- GitHub Actions workflow (`.github/workflows/deploy.yml`) for linting, testing, Docker image build, Artifact Registry upload, and Cloud Run deployment.

## Non-Functional Requirements
- **Test Coverage:** Unit test coverage > 80% across all modules (`pytest`, `pytest-asyncio`).
- **Reliability:** Zero telemetry message loss during network disconnects.
- **Portability:** Operates seamlessly on local Linux/macOS/Windows environments, Docker containers, and GCP Cloud Run.

## Acceptance Criteria
- [ ] Protobuf schema compiles without errors and generates Python classes.
- [ ] CSV mock generator correctly parses multi-bin spectral CSV rows and emits Protobuf objects.
- [ ] SQLite spooler buffers messages during simulated outage and drains successfully upon reconnection.
- [ ] GCP Pub/Sub client publishes to emulator or mock transport cleanly.
- [ ] `/healthz` returns `200 OK` and `/metrics` exposes Prometheus counters.
- [ ] All unit tests pass with >80% code coverage.
- [ ] Docker container builds cleanly and runs.

## Out of Scope (for MVP)
- Real physical SDR hardware bindings (e.g., `librtlsdr`, `SoapySDR`) — deferred to post-MVP hardware integration tracks.
- Complex multi-tenant authentication protocols beyond GCP ADC / Service Accounts.
