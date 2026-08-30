# Product Guidelines: GCP RF Telemetry Collector Agent

## User Experience & Interface
- **CLI & Container UX:** Clean, human-readable console output and standard CLI flags (`--config`, `--csv-file`, `--dry-run`, `--log-level`).
- **Configuration UX:** Zero-friction configuration via environment variables (12-Factor App methodology) or YAML config file with sensible defaults.

## Logging & Observability Standards
- **GCP Structured Logging:** Format JSON log output strictly matching GCP Cloud Logging (Stackdriver) standard schema (`severity`, `message`, `timestamp`, `component`, `trace`).
- **Prometheus Metrics:** Expose an HTTP `/metrics` endpoint for Prometheus scraping of agent operational metrics (messages processed, dropped, spooled, GCP latency).
- **Metric Privacy & Security:** Ensure no sensitive GCP credentials or private keys are exposed in log output.
- **Health Probes:** Provide container health check endpoints (`/healthz`, `/livez`) for Docker and GCP Cloud Run probes.

## Error Handling & Reliability Principles
- **Fail-Safe Operation:** Transient network errors communicating with GCP Pub/Sub or Cloud Run must trigger automatic exponential backoff retry logic.
- **Graceful Shutdown:** Handle `SIGINT` / `SIGTERM` signals cleanly by flushing in-memory telemetry buffers to local SQLite spooling before container termination.
- **Clear Diagnostic Messages:** Error messages must contain actionable context (e.g. Pub/Sub Topic name, HTTP status code, SQLite spool path).

## Code & Architecture Quality
- **Modular Component Design:** Decouple RF Data Source (Hardware vs Mock CSV Generator), Serialization (Protobuf), Storage/Spooling (SQLite), and Cloud Transporters (GCP Pub/Sub / Cloud Run API).
- **Test-Driven Development (TDD):** Implement unit tests for Protobuf encoder/decoder, CSV mock generator, offline queue buffer, and GCP pub/sub client mock.
