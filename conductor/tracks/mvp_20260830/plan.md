# Implementation Plan: MVP Implementation Track

## Phase 1: Environment & Project Scaffolding [checkpoint: 1e71a7b]
- [x] Task: Environment Setup & Python Dependency Management (`pyproject.toml`) [1e71a7b]
  - [x] Create `pyproject.toml` with dependencies (`google-cloud-pubsub`, `protobuf`, `fastapi`, `uvicorn`, `prometheus-client`, `aiosqlite`, `pytest`, `pytest-asyncio`, `ruff`).
  - [x] Configure package directory structure (`src/agent/`, `tests/`, `proto/`, `data/`).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [1e71a7b]

## Phase 2: Protobuf Schema Definition & Codegen Module [checkpoint: 3e8bf68]
- [x] Task: Write Unit Tests for Protobuf Serialization & Deserialization [3e8bf68]
  - [x] Write unit tests in `tests/test_proto.py` for Protobuf schema instantiation, serialization, and deserialization.
- [x] Task: Implement Protobuf Telemetry Schema (`proto/telemetry.proto`) & Codegen Script [3e8bf68]
  - [x] Write `proto/telemetry.proto` with `RfTelemetryMessage` schema supporting spectral sweep data (`db_bins`).
  - [x] Add build/compilation script to compile `.proto` to Python module `src/agent/proto/telemetry_pb2.py`.
  - [x] Rerun unit tests and confirm all tests pass (Green Phase).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [3e8bf68]

## Phase 3: CSV Mock Reader & Telemetry Data Ingestion [checkpoint: 2aed756]
- [x] Task: Write Unit Tests for CSV Mock Reader [2aed756]
  - [x] Create sample test CSV file in `tests/fixtures/sample_rf.csv`.
  - [x] Write failing unit tests in `tests/test_csv_reader.py` for parsing CSV rows, validating spectral fields (`date, time, hz_low, hz_high, hz_bin_width, num_samples, dB...`), and converting to Protobuf messages.
- [x] Task: Implement CSV Mock Reader Module (`src/agent/csv_reader.py`) [2aed756]
  - [x] Implement `CsvTelemetryReader` class with async generator yielding `RfTelemetryMessage` objects.
  - [x] Run unit tests and confirm all tests pass (Green Phase).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [2aed756]

## Phase 4: SQLite Offline Queue & Buffer Spooler [checkpoint: 4aab870]
- [x] Task: Write Unit Tests for SQLite Spooler [4aab870]
  - [x] Write failing unit tests in `tests/test_spooler.py` for enqueueing Protobuf payloads, persistent disk storage, dequeueing in FIFO order, and queue size metrics.
- [x] Task: Implement SQLite Spooler Module (`src/agent/spooler.py`) [4aab870]
  - [x] Implement async `SqliteSpooler` class backed by SQLite database.
  - [x] Run unit tests and confirm all tests pass (Green Phase).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [4aab870]

## Phase 5: GCP Pub/Sub Transport & Mock Publisher Client [checkpoint: d5005c3]
- [x] Task: Write Unit Tests for Pub/Sub Transport & Mock Publisher [d5005c3]
  - [x] Write failing unit tests in `tests/test_publisher.py` for GCP Pub/Sub client publishing, local mock publisher mode, and automatic fallback to SQLite spooler on network failure.
- [x] Task: Implement GCP Pub/Sub Publisher Module (`src/agent/publisher.py`) [d5005c3]
  - [x] Implement `PubSubPublisher` supporting `google-cloud-pubsub` and mock transport.
  - [x] Run unit tests and confirm all tests pass (Green Phase).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [d5005c3]

## Phase 6: FastAPI Observability Server & Agent Pipeline CLI [checkpoint: 0670033]
- [x] Task: Write Unit Tests for Observability Server & CLI Pipeline [0670033]
  - [x] Write failing unit tests in `tests/test_server.py` for `GET /healthz` and `GET /metrics`.
  - [x] Write failing integration test in `tests/test_pipeline.py` for end-to-end telemetry ingestion, spooling, and publishing.
- [x] Task: Implement Observability Server & Agent Orchestrator CLI (`src/agent/server.py` & `src/agent/cli.py`) [0670033]
  - [x] Implement FastAPI server exposing health and Prometheus metrics.
  - [x] Implement main agent loop connecting CSV reader -> Spooler -> Pub/Sub publisher.
  - [x] Run all unit & integration tests and verify >80% test coverage.
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [0670033]

## Phase 7: Docker Containerization & GitHub Actions CI/CD
- [x] Task: Create Dockerfile & Docker Compose Setup [1fa5d5b]
  - [x] Create multi-stage `Dockerfile` and `docker-compose.yml` for local container execution and Pub/Sub emulator integration.
  - [x] Verify local container build and execution.
- [x] Task: Implement GitHub Actions CI/CD Workflow (`.github/workflows/deploy.yml`) [1fa5d5b]
  - [x] Create workflow file for running unit tests, building Docker image, uploading to Google Artifact Registry, and deploying to Cloud Run.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
