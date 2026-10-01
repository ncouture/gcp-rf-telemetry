"""Unit tests for Sniffle BLE streaming JSON reader."""

from pathlib import Path

import pytest

from agent.sniffle_reader import SniffleJsonReader


@pytest.fixture
def sample_fixture_path():
    return Path(__file__).parent / "fixtures" / "sample_sniffle.json"


@pytest.mark.asyncio
async def test_sniffle_reader_parses_sample_packets(sample_fixture_path):
    reader = SniffleJsonReader(
        json_path=sample_fixture_path,
        loop=False,
        interval_sec=0.0,
    )

    messages = []
    async for msg in reader.read_telemetry():
        messages.append(msg)

    assert len(messages) > 0
    first_msg = messages[0]
    assert first_msg.device_id.startswith("sniffle")
    assert first_msg.channel == 0
    assert first_msg.signal_dbm == -57
    assert first_msg.access_address == "0x8e89bed6"
    assert first_msg.pdu_type == "SCAN_REQ"
    assert first_msg.advertiser_mac == "08:30:dc:4e:3d:3c"
    assert first_msg.scanner_mac == "6a:b6:b8:68:bc:d8"
    assert first_msg.crc_valid is True


@pytest.mark.asyncio
async def test_sniffle_reader_min_rssi_filter(sample_fixture_path):
    # Set min_rssi to -40 dBm; in sample fixture only packet 9 has signal_dbm == -37
    reader = SniffleJsonReader(
        json_path=sample_fixture_path,
        min_rssi=-40,
        loop=False,
        interval_sec=0.0,
    )

    messages = []
    async for msg in reader.read_telemetry():
        messages.append(msg)

    assert len(messages) == 1
    assert messages[0].signal_dbm == -37
    assert messages[0].advertiser_mac == "46:84:6d:6e:ce:f9"


@pytest.mark.asyncio
async def test_sniffle_reader_eir_extraction(sample_fixture_path):
    reader = SniffleJsonReader(
        json_path=sample_fixture_path,
        loop=False,
        interval_sec=0.0,
    )

    messages = []
    async for msg in reader.read_telemetry():
        messages.append(msg)

    # Packet 9 has device_name "NJBPL"
    named_packets = [m for m in messages if m.device_name == "NJBPL"]
    assert len(named_packets) == 1
    assert named_packets[0].advertiser_mac == "46:84:6d:6e:ce:f9"

    # Packet 4 has company_id "0x004c" (Apple)
    apple_packets = [m for m in messages if m.company_id == "0x004c"]
    assert len(apple_packets) >= 1


@pytest.mark.asyncio
async def test_sniffle_reader_file_not_found():
    reader = SniffleJsonReader(json_path="non_existent_capture.json")
    with pytest.raises(FileNotFoundError):
        async for _ in reader.read_telemetry():
            pass


@pytest.mark.asyncio
async def test_sniffle_reader_realtime_and_interval(sample_fixture_path):
    reader = SniffleJsonReader(
        json_path=sample_fixture_path,
        realtime=True,
        loop=False,
    )
    count = 0
    async for _ in reader.read_telemetry():
        count += 1
        if count >= 3:
            break
    assert count == 3
