"""Unit tests for SQLite spooling buffer queue."""

import pytest
from pathlib import Path
from agent.proto.telemetry_pb2 import RfTelemetryMessage


@pytest.mark.asyncio
async def test_sqlite_spooler_enqueue_dequeue(tmp_path: Path):
    from agent.spooler import SqliteSpooler

    db_file = tmp_path / "test_spool.db"
    spooler = SqliteSpooler(db_path=db_file)
    await spooler.initialize()

    assert await spooler.get_queue_size() == 0

    msg1 = RfTelemetryMessage(
        device_id="sensor-1",
        timestamp_iso="2026-08-30T01:00:00Z",
        hz_low=100.0,
        hz_high=200.0,
        db_bins=[-50.0],
    )
    msg2 = RfTelemetryMessage(
        device_id="sensor-2",
        timestamp_iso="2026-08-30T01:00:01Z",
        hz_low=200.0,
        hz_high=300.0,
        db_bins=[-45.0],
    )

    await spooler.enqueue(msg1)
    await spooler.enqueue(msg2)

    assert await spooler.get_queue_size() == 2

    # Dequeue batch of 1
    batch1 = await spooler.peek_batch(batch_size=1)
    assert len(batch1) == 1
    id1, peek_msg1 = batch1[0]
    assert peek_msg1.device_id == "sensor-1"

    await spooler.delete_batch([id1])
    assert await spooler.get_queue_size() == 1

    # Dequeue remaining
    batch2 = await spooler.peek_batch(batch_size=10)
    assert len(batch2) == 1
    id2, peek_msg2 = batch2[0]
    assert peek_msg2.device_id == "sensor-2"

    await spooler.delete_batch([id2])
    assert await spooler.get_queue_size() == 0

    await spooler.close()
