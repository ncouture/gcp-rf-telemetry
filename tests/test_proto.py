"""Unit tests for Protobuf schema serialization and deserialization."""

import pytest


def test_rf_telemetry_message_serialization():
    from agent.proto.telemetry_pb2 import RfTelemetryMessage

    msg = RfTelemetryMessage(
        device_id="sensor-001",
        timestamp_iso="2026-08-30T01:00:00Z",
        timestamp_epoch_ms=1788051600000,
        hz_low=1000000.0,
        hz_high=2000000.0,
        hz_bin_width=10000.0,
        num_samples=100,
        db_bins=[-50.5, -48.2, -60.1, -45.0],
    )

    serialized = msg.SerializeToString()
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0

    deserialized = RfTelemetryMessage()
    deserialized.ParseFromString(serialized)

    assert deserialized.device_id == "sensor-001"
    assert deserialized.timestamp_iso == "2026-08-30T01:00:00Z"
    assert deserialized.timestamp_epoch_ms == 1788051600000
    assert deserialized.hz_low == 1000000.0
    assert deserialized.hz_high == 2000000.0
    assert deserialized.hz_bin_width == 10000.0
    assert deserialized.num_samples == 100
    assert list(deserialized.db_bins) == pytest.approx([-50.5, -48.2, -60.1, -45.0])
