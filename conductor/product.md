# Product Definition: GCP RF Telemetry Collector Agent

## Vision & Overview
The **GCP RF Telemetry Collector Agent** is a containerized IoT/Edge service designed to capture Radio Frequency (RF) telemetry signals from local edge sensors/hardware or a configurable mock generator. It serializes sensor data and signal metrics using Protocol Buffers (Protobuf) and streams them reliably to Google Cloud Platform (GCP) Cloud Pub/Sub and Cloud Run backends for real-time monitoring, processing, and centralized analytics.

## Key Target Environment
- **Deployment Model:** Containerized Edge Container (Docker / Podman) & GCP Cloud Run integration
- **Target OS:** Linux Edge Gateways, Embedded Systems, and Cloud Run containers

## Core Capabilities
- **RF Telemetry Ingestion & Mocking:** Ingests RF hardware telemetry or simulates data via a mock generator reading static CSV files for local development and testing.
- **RF Signal Metrics Tracking:** Real-time capture of frequency, RSSI, SNR, sample rate, and packet error rates.
- **Protobuf Serialization:** Low-overhead, strongly typed binary encoding for RF telemetry payloads.
- **GCP Streaming Transport:** Direct publishing of telemetry messages to GCP Cloud Pub/Sub via gRPC / REST APIs with GCP Application Default Credentials (ADC) / Cloud Run environment authentication.
- **Offline Resilience & Buffering:** Local disk spooling / SQLite queue to persist telemetry messages during GCP connectivity loss and drain upon reconnection.
- **Automated CI/CD:** GitHub Actions workflows for automated Docker container builds, Google Artifact Registry storage, and GCP Cloud Run deployments.

## Non-Functional Requirements
- **Performance:** Low CPU/memory footprint suitable for edge container runtimes.
- **Reliability:** Zero telemetry loss during transient network disconnects via local disk buffering.
- **Observability:** Structured logging and health metrics for container diagnostics.
