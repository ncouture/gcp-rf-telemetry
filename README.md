# GCP RF Telemetry Collector Agent

An IoT/Edge data collector agent designed to capture Radio Frequency (RF) telemetry signals from local sensors or mock CSV files and stream them reliably to Google Cloud Platform (GCP) Cloud Pub/Sub and Cloud Run services.

## Overview
- **Protobuf Serialization:** Compact binary encoding of spectral sweep telemetry data.
- **Offline Resilience:** SQLite disk spooling queue for zero telemetry loss during network outages.
- **Observability:** FastAPI `/healthz` and Prometheus `/metrics` endpoint.
- **Containerized Deployment:** Docker runtime and GitHub Actions CI/CD to GCP Cloud Run.
