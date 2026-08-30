"""Unit tests for GCP Pub/Sub Publisher and Mock Transport."""

from pathlib import Path

import pytest

from agent.proto.telemetry_pb2 import RfTelemetryMessage
from agent.publisher import PubSubPublisher
from agent.spooler import SqliteSpooler


@pytest.mark.asyncio
async def test_mock_publisher_publish_success():
    publisher = PubSubPublisher(
        project_id="test-gcp-project",
        topic_id="test-rf-topic",
        mock_mode=True,
    )
    await publisher.initialize()

    msg = RfTelemetryMessage(
        device_id="sensor-01",
        timestamp_iso="2026-08-30T01:00:00Z",
        hz_low=100.0,
        hz_high=200.0,
        db_bins=[-50.0, -45.0],
    )

    published_id = await publisher.publish(msg)
    assert published_id is not None
    assert isinstance(published_id, str)
    assert len(publisher.mock_published_messages) == 1
    assert publisher.mock_published_messages[0].device_id == "sensor-01"


@pytest.mark.asyncio
async def test_publisher_spool_fallback_on_failure(tmp_path: Path):
    spooler = SqliteSpooler(db_path=tmp_path / "fallback.db")
    await spooler.initialize()

    publisher = PubSubPublisher(
        project_id="test-gcp-project",
        topic_id="test-rf-topic",
        mock_mode=True,
        mock_simulate_failure=True,
        spooler=spooler,
    )
    await publisher.initialize()

    msg = RfTelemetryMessage(
        device_id="sensor-offline",
        timestamp_iso="2026-08-30T01:00:00Z",
        hz_low=100.0,
        hz_high=200.0,
    )

    published_id = await publisher.publish(msg)
    assert published_id is None  # Publishing failed, spooled to disk
    assert await spooler.get_queue_size() == 1

    await spooler.close()


@pytest.mark.asyncio
async def test_publisher_drain_spooler(tmp_path: Path):
    spooler = SqliteSpooler(db_path=tmp_path / "drain.db")
    await spooler.initialize()

    msg = RfTelemetryMessage(
        device_id="sensor-spooled",
        timestamp_iso="2026-08-30T01:00:00Z",
        hz_low=100.0,
        hz_high=200.0,
    )
    await spooler.enqueue(msg)
    assert await spooler.get_queue_size() == 1

    # Publisher online, drain spooler
    publisher = PubSubPublisher(
        project_id="test-gcp-project",
        topic_id="test-rf-topic",
        mock_mode=True,
        spooler=spooler,
    )
    await publisher.initialize()

    drained_count = await publisher.drain_spooler()
    assert drained_count == 1
    assert await spooler.get_queue_size() == 0
    assert len(publisher.mock_published_messages) == 1

    await spooler.close()


@pytest.mark.asyncio
async def test_publisher_emulator_env_init(monkeypatch):
    monkeypatch.setenv("PUBSUB_EMULATOR_HOST", "localhost:8085")
    publisher = PubSubPublisher(project_id="emu-proj", topic_id="emu-topic")
    await publisher.initialize()
    assert publisher._topic_path == "projects/emu-proj/topics/emu-topic"
