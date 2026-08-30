"""Unit tests for CSV mock telemetry reader."""

from pathlib import Path

import pytest

from agent.csv_reader import CsvTelemetryReader
from agent.proto.telemetry_pb2 import RfTelemetryMessage


@pytest.mark.asyncio
async def test_csv_telemetry_reader_parse():
    fixture_path = Path(__file__).parent / "fixtures" / "sample_rf.csv"
    reader = CsvTelemetryReader(
        csv_path=fixture_path, device_id="test-sensor-1", loop=False, interval_sec=0.0
    )

    messages = []
    async for msg in reader.read_telemetry():
        assert isinstance(msg, RfTelemetryMessage)
        messages.append(msg)

    assert len(messages) == 2
    first = messages[0]
    assert first.device_id == "test-sensor-1"
    assert first.timestamp_iso == "2026-08-30T01:00:00Z"
    assert first.hz_low == 100000000.0
    assert first.hz_high == 100040000.0
    assert first.hz_bin_width == 10000.0
    assert first.num_samples == 4
    assert list(first.db_bins) == pytest.approx([-55.1, -48.3, -62.0, -50.2])


@pytest.mark.asyncio
async def test_csv_telemetry_reader_file_not_found():
    reader = CsvTelemetryReader(csv_path="non_existent.csv", loop=False, interval_sec=0.0)
    with pytest.raises(FileNotFoundError):
        async for _ in reader.read_telemetry():
            pass


def test_csv_telemetry_reader_invalid_row_handling():
    reader = CsvTelemetryReader(csv_path="dummy.csv")
    assert reader.parse_row_tokens([], []) is None

    # Missing date/time fallback + dB prefix headers
    header = ["hz_low", "hz_high", "hz_bin_width", "num_samples", "dB_1", "dB_2"]
    row = ["100", "200", "10", "2", "-40.0", "-42.5"]
    msg = reader.parse_row_tokens(header, row)
    assert msg is not None
    assert msg.hz_low == 100.0
    assert msg.hz_high == 200.0
    assert list(msg.db_bins) == pytest.approx([-40.0, -42.5])
