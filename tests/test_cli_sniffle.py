"""Unit tests for CLI with Sniffle BLE JSON ingestion."""

from pathlib import Path

import pytest

from agent.cli import main_async, parse_args


@pytest.fixture
def sample_fixture_path():
    return Path(__file__).parent / "fixtures" / "sample_sniffle.json"


def test_cli_parse_args_sniffle():
    args = parse_args(
        [
            "--sniffle-json",
            "tests/fixtures/sample_sniffle.json",
            "--min-rssi",
            "-70",
            "--realtime",
            "--ble-topic-id",
            "custom-ble-topic",
        ]
    )
    assert args.sniffle_json == "tests/fixtures/sample_sniffle.json"
    assert args.min_rssi == -70
    assert args.realtime is True
    assert args.ble_topic_id == "custom-ble-topic"


@pytest.mark.asyncio
async def test_cli_dry_run_sniffle(sample_fixture_path, capsys):
    args = parse_args(
        [
            "--sniffle-json",
            str(sample_fixture_path),
            "--dry-run",
        ]
    )
    await main_async(args)
    captured = capsys.readouterr()
    assert "Starting GCP RF Telemetry Agent with Sniffle BLE JSON" in captured.out
    assert "Dry run complete. Total messages read:" in captured.out
    assert "Read BLE packet" in captured.out
