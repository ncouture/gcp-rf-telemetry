"""Unit and integration tests for BLE telemetry pipeline and publisher."""

from pathlib import Path

import pytest

from agent.pipeline import TelemetryPipeline
from agent.proto.telemetry_pb2 import BleAdvertisementMessage, RfTelemetryMessage
from agent.publisher import PubSubPublisher
from agent.sniffle_reader import SniffleJsonReader
from agent.spooler import SqliteSpooler


@pytest.fixture
def sample_fixture_path():
    return Path(__file__).parent / "fixtures" / "sample_sniffle.json"


@pytest.mark.asyncio
async def test_spooler_polymorphic_storage(tmp_path):
    db_file = tmp_path / "test_polymorphic_spool.db"
    spooler = SqliteSpooler(db_path=db_file)
    await spooler.initialize()

    ble_msg = BleAdvertisementMessage(
        device_id="sniffle-01",
        advertiser_mac="11:22:33:44:55:66",
        signal_dbm=-48,
    )
    rf_msg = RfTelemetryMessage(
        device_id="hackrf-01",
        hz_low=100.0,
        hz_high=200.0,
        db_bins=[-60.0, -55.0],
    )

    await spooler.enqueue(ble_msg)
    await spooler.enqueue(rf_msg)

    assert await spooler.get_queue_size() == 2

    batch = await spooler.peek_batch(10)
    assert len(batch) == 2

    id1, msg1 = batch[0]
    id2, msg2 = batch[1]

    assert isinstance(msg1, BleAdvertisementMessage)
    assert msg1.advertiser_mac == "11:22:33:44:55:66"

    assert isinstance(msg2, RfTelemetryMessage)
    assert msg2.device_id == "hackrf-01"

    await spooler.delete_batch([id1, id2])
    assert await spooler.get_queue_size() == 0
    await spooler.close()


@pytest.mark.asyncio
async def test_publisher_ble_message_mock_mode():
    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="rf-telemetry-stream",
        ble_topic_id="ble-telemetry-stream",
        mock_mode=True,
    )
    await publisher.initialize()

    ble_msg = BleAdvertisementMessage(
        device_id="sniffle-01",
        advertiser_mac="aa:bb:cc:dd:ee:ff",
        signal_dbm=-50,
    )

    msg_id = await publisher.publish(ble_msg)
    assert msg_id is not None
    assert len(publisher.mock_published_messages) == 1
    assert publisher.mock_published_messages[0].advertiser_mac == "aa:bb:cc:dd:ee:ff"


@pytest.mark.asyncio
async def test_pipeline_sniffle_integration(sample_fixture_path, tmp_path):
    db_file = tmp_path / "pipeline_ble_spool.db"
    spooler = SqliteSpooler(db_path=db_file)
    await spooler.initialize()

    publisher = PubSubPublisher(
        project_id="test-project",
        topic_id="telemetry-stream",
        mock_mode=True,
        spooler=spooler,
    )
    await publisher.initialize()

    reader = SniffleJsonReader(
        json_path=sample_fixture_path,
        loop=False,
        interval_sec=0.0,
    )

    pipeline = TelemetryPipeline(reader=reader, publisher=publisher, spooler=spooler)
    count = await pipeline.run_once()

    assert count > 0
    assert len(publisher.mock_published_messages) == count
    await spooler.close()
