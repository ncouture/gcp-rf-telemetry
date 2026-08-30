"""Integration tests for end-to-end TelemetryPipeline."""

import pytest
from pathlib import Path

from agent.csv_reader import CsvTelemetryReader
from agent.publisher import PubSubPublisher
from agent.spooler import SqliteSpooler
from agent.pipeline import TelemetryPipeline


@pytest.mark.asyncio
async def test_telemetry_pipeline_end_to_end(tmp_path: Path):
    csv_path = Path(__file__).parent / "fixtures" / "sample_rf.csv"
    reader = CsvTelemetryReader(csv_path=csv_path, loop=False, interval_sec=0.0)

    spooler = SqliteSpooler(db_path=tmp_path / "pipeline.db")
    await spooler.initialize()

    publisher = PubSubPublisher(mock_mode=True, spooler=spooler)
    await publisher.initialize()

    pipeline = TelemetryPipeline(reader=reader, publisher=publisher, spooler=spooler)

    processed_count = await pipeline.run_once()
    assert processed_count == 2
    assert len(publisher.mock_published_messages) == 2
    assert await spooler.get_queue_size() == 0

    await spooler.close()


@pytest.mark.asyncio
async def test_telemetry_pipeline_offline_spool_flow(tmp_path: Path):
    csv_path = Path(__file__).parent / "fixtures" / "sample_rf.csv"
    reader = CsvTelemetryReader(csv_path=csv_path, loop=False, interval_sec=0.0)

    spooler = SqliteSpooler(db_path=tmp_path / "offline_pipeline.db")
    await spooler.initialize()

    # Simulate GCP Pub/Sub network failure
    publisher = PubSubPublisher(
        mock_mode=True, mock_simulate_failure=True, spooler=spooler
    )
    await publisher.initialize()

    pipeline = TelemetryPipeline(reader=reader, publisher=publisher, spooler=spooler)

    processed_count = await pipeline.run_once()
    assert processed_count == 2
    assert len(publisher.mock_published_messages) == 0
    assert await spooler.get_queue_size() == 2

    # Now restore network connection and run pipeline again to drain
    publisher.mock_simulate_failure = False
    await publisher.drain_spooler()
    assert await spooler.get_queue_size() == 0
    assert len(publisher.mock_published_messages) == 2

    await spooler.close()
