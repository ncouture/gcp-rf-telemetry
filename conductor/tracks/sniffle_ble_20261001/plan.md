# Implementation Plan: Sniffle BLE Advertisement Scans Ingestion Track

## Phase 1: Test Fixtures & Protobuf Schema Expansion [checkpoint: 890c871]
- [x] Task: Write Unit Tests for `BleAdvertisementMessage` and `TelemetryEnvelope` [890c871]
  - [x] Create small representative JSON fixture `tests/fixtures/sample_sniffle.json` (extracted from `sniffle.json`).
  - [x] Write unit tests in `tests/test_proto_ble.py` for `BleAdvertisementMessage` and `TelemetryEnvelope` serialization and deserialization.
- [x] Task: Update `proto/telemetry.proto` & Run Codegen [890c871]
  - [x] Add `BleAdvertisementMessage` and `TelemetryEnvelope` to `proto/telemetry.proto`.
  - [x] Run `scripts/compile_proto.py` and verify all proto unit tests pass (Green Phase).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [890c871]

## Phase 2: Streaming Sniffle JSON Reader Implementation [checkpoint: ee2b279]
- [x] Task: Write Unit Tests for `SniffleJsonReader` [ee2b279]
  - [x] Write failing unit tests in `tests/test_sniffle_reader.py` testing packet parsing, field extraction (MAC, RSSI, channel, PDU type, device name, company ID), CRC filtering, and minimum RSSI threshold.
- [x] Task: Implement `SniffleJsonReader` (`src/agent/sniffle_reader.py`) [ee2b279]
  - [x] Implement streaming JSON parser that yields `BleAdvertisementMessage` objects one-by-one with constant memory overhead.
  - [x] Implement CRC validation filter and `--min-rssi` threshold filter.
  - [x] Implement timing pacing (real-time delta vs fixed interval).
  - [x] Verify all reader tests pass (Green Phase).
- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md) [ee2b279]

## Phase 3: Pipeline & Publisher Dual-Source Integration
- [x] Task: Write Unit & Integration Tests for BLE Telemetry Ingestion [7ff6d50]
  - [x] Write failing tests in `tests/test_pipeline_ble.py` verifying that `TelemetryPipeline` and `PubSubPublisher` correctly handle `BleAdvertisementMessage`, persist to SQLite spooler if offline, and publish with appropriate attributes.
- [x] Task: Update `PubSubPublisher`, `TelemetryPipeline`, and `SqliteSpooler` [7ff6d50]
  - [x] Enhance `PubSubPublisher` to support publishing BLE messages and optional dedicated `--ble-topic-id`.
  - [x] Enhance `TelemetryPipeline` to accept any telemetry reader (CSV or Sniffle JSON).
  - [x] Ensure `SqliteSpooler` supports serializing both message types.
  - [x] Verify all tests pass (Green Phase).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 4: CLI Integration, Observability & Verification
- [ ] Task: Update Observability & CLI Entrypoint
  - [ ] Add Prometheus metrics `ble_packets_processed_total` and `ble_packets_crc_errors_total` to `src/agent/server.py`.
  - [ ] Add `--sniffle-json`, `--min-rssi`, `--realtime`, `--ble-topic-id` arguments to `src/agent/cli.py`.
  - [ ] Add unit tests in `tests/test_cli_sniffle.py` for CLI dry-run and argument parsing with Sniffle JSON.
- [ ] Task: End-to-End Stress Verification & Readme Documentation
  - [ ] Verify execution against the full 73MB `sniffle.json` in dry-run mode.
  - [ ] Run full test suite and `ruff check .` ensuring >80% coverage and zero lint errors.
  - [ ] Update `README.md` to document the new Sniffle BLE capabilities and CLI flags.
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
