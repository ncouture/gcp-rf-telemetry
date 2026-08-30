# Implementation Plan: MVP Implementation Track

## Phase 1: Environment & Project Scaffolding [checkpoint: 1e71a7b]
- [x] Task: Environment Setup & Python Dependency Management (`pyproject.toml`) [1e71a7b]
  - [x] Create `pyproject.toml` with dependencies (`google-cloud-pubsub`, `protobuf`, `fastapi`, `uvicorn`, `prometheus-client`, `aiosqlite`, `pytest`, `pytest-asyncio`, `ruff`).
  - [x] Configure package directory structure (`src/agent/`, `tests/`, `proto/`, `data/`).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [1e71a7b]

## Phase 2: Protobuf Schema Definition & Codegen Module
- [x] Task: Write Unit Tests for Protobuf Serialization & Deserialization [3e8bf68]
  - [x] Write unit tests in `tests/test_proto.py` for Protobuf schema instantiation, serialization, and deserialization.
- [x] Task: Implement Protobuf Telemetry Schema (`proto/telemetry.proto`) & Codegen Script [3e8bf68]
  - [x] Write `proto/telemetry.proto` with `RfTelemetryMessage` schema supporting spectral sweep data (`db_bins`).
  - [x] Add build/compilation script to compile `.proto` to Python module `src/agent/proto/telemetry_pb2.py`.
  - [x] Rerun unit tests and confirm all tests pass (Green Phase).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: CSV Mock Reader & Telemetry Data Ingestion
- [ ] Task: Write Unit Tests for CSV Mock Reader
  - [ ] Create sample test CSV file in `tests/fixtures/sample_rf.csv`.
  - [ ] Write failing unit tests in `tests/test_csv_reader.py` for parsing CSV rows, validating spectral fields (`date, time, hz_low, hz_high, hz_bin_width, num_samples, dB...`), and converting to Protobuf messages.
- [ ] Task: Implement CSV Mock Reader Module (`src/agent/csv_reader.py`)
  - [ ] Implement `CsvTelemetryReader` class with async generator yielding `RfTelemetryMessage` objects.
  - [ ] Run unit tests and confirm all tests pass (Green Phase).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 4: SQLite Offline Queue & Buffer Spooler
- [ ] Task: Write Unit Tests for SQLite Spooler
  - [ ] Write failing unit tests in `tests/test_spooler.py` for enqueueing Protobuf payloads, persistent disk storage, dequeueing in FIFO order, and queue size metrics.
- [ ] Task: Implement SQLite Spooler Module (`src/agent/spooler.py`)
  - [ ] Implement async `SqliteSpooler` class backed by SQLite database.
  - [ ] Run unit tests and confirm all tests pass (Green Phase).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 5: GCP Pub/Sub Transport & Mock Publisher Client
- [ ] Task: Write Unit Tests for Pub/Sub Transport & Mock Publisher
  - [ ] Write failing unit tests in `tests/test_publisher.py` for GCP Pub/Sub client publishing, local mock publisher mode, and automatic fallback to SQLite spooler on network failure.
- [ ] Task: Implement GCP Pub/Sub Publisher Module (`src/agent/publisher.py`)
  - [ ] Implement `PubSubPublisher` supporting `google-cloud-pubsub` and mock transport.
  - [ ] Run unit tests and confirm all tests pass (Green Phase).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 6: FastAPI Observability Server & Agent Pipeline CLI
- [ ] Task: Write Unit Tests for Observability Server & CLI Pipeline
  - [ ] Write failing unit tests in `tests/test_server.py` for `GET /healthz` and `GET /metrics`.
  - [ ] Write failing integration test in `tests/test_pipeline.py` for end-to-end telemetry ingestion, spooling, and publishing.
- [ ] Task: Implement Observability Server & Agent Orchestrator CLI (`src/agent/server.py` & `src/agent/cli.py`)
  - [ ] Implement FastAPI server exposing health and Prometheus metrics.
  - [ ] Implement main agent loop connecting CSV reader -> Spooler -> Pub/Sub publisher.
  - [ ] Run all unit & integration tests and verify >80% test coverage.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 7: Docker Containerization & GitHub Actions CI/CD
- [ ] Task: Create Dockerfile & Docker Compose Setup
  - [ ] Create multi-stage `Dockerfile` and `docker-compose.yml` for local container execution and Pub/Sub emulator integration.
  - [ ] Verify local container build and execution.
- [ ] Task: Implement GitHub Actions CI/CD Workflow (`.github/workflows/deploy.yml`)
  - [ ] Create workflow file for running unit tests, building Docker image, uploading to Google Artifact Registry, and deploying to Cloud Run.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
