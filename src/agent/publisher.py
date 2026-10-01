"""GCP Cloud Pub/Sub Publisher Transport Module."""

import asyncio
import os
import uuid

from agent.proto.telemetry_pb2 import (
    BleAdvertisementMessage,
    RfTelemetryMessage,
    TelemetryEnvelope,
)
from agent.spooler import SqliteSpooler


class PubSubPublisher:
    """Async publisher for GCP Cloud Pub/Sub with mock mode & offline spooler fallback."""

    def __init__(
        self,
        project_id: str = "gcp-rf-telemetry",
        topic_id: str = "rf-telemetry-stream",
        ble_topic_id: str | None = None,
        mock_mode: bool = False,
        mock_simulate_failure: bool = False,
        spooler: SqliteSpooler | None = None,
    ) -> None:
        self.project_id = project_id
        self.topic_id = topic_id
        self.ble_topic_id = ble_topic_id or topic_id
        self.mock_mode = mock_mode
        self.mock_simulate_failure = mock_simulate_failure
        self.spooler = spooler

        self._publisher_client = None
        self._topic_path: str | None = None
        self._ble_topic_path: str | None = None
        self.mock_published_messages: list[
            RfTelemetryMessage | BleAdvertisementMessage | TelemetryEnvelope
        ] = []

    async def initialize(self) -> None:
        """Initializes GCP Pub/Sub publisher client unless running in mock mode."""
        self._topic_path = f"projects/{self.project_id}/topics/{self.topic_id}"
        self._ble_topic_path = f"projects/{self.project_id}/topics/{self.ble_topic_id}"

        if self.mock_mode or "PUBSUB_EMULATOR_HOST" in os.environ:
            return

        try:
            from google.cloud import pubsub_v1

            self._publisher_client = pubsub_v1.PublisherClient()
            self._topic_path = self._publisher_client.topic_path(
                self.project_id, self.topic_id
            )
            self._ble_topic_path = self._publisher_client.topic_path(
                self.project_id, self.ble_topic_id
            )
        except (RuntimeError, ValueError, OSError, AttributeError) as e:
            print(f"Warning: Failed to initialize GCP Pub/Sub client ({e}). Switching to mock mode.")
            self.mock_mode = True

    async def publish(
        self,
        message: RfTelemetryMessage | BleAdvertisementMessage | TelemetryEnvelope,
    ) -> str | None:
        """Publishes a telemetry message to GCP Pub/Sub. Spools to disk on failure."""
        if self._topic_path is None or self._ble_topic_path is None:
            await self.initialize()

        if self.mock_mode:
            if self.mock_simulate_failure:
                if self.spooler is not None:
                    await self.spooler.enqueue(message)
                return None

            self.mock_published_messages.append(message)
            return str(uuid.uuid4())

        is_ble = isinstance(message, BleAdvertisementMessage)
        target_topic = self._ble_topic_path if is_ble else self._topic_path
        telemetry_type = "ble_advertisement" if is_ble else "spectral_sweep"
        device_id = getattr(message, "device_id", "unknown")
        timestamp_iso = getattr(message, "timestamp_iso", "")

        payload = message.SerializeToString()
        try:
            loop = asyncio.get_running_loop()
            future = self._publisher_client.publish(
                target_topic,
                data=payload,
                device_id=device_id,
                timestamp=timestamp_iso,
                telemetry_type=telemetry_type,
            )
            msg_id = await loop.run_in_executor(None, future.result)
            return str(msg_id)
        except (RuntimeError, ValueError, OSError) as e:
            print(f"GCP Pub/Sub publish failed ({e}). Spooling message to offline buffer...")
            if self.spooler is not None:
                await self.spooler.enqueue(message)
            return None

    async def drain_spooler(self, max_batch: int = 50) -> int:
        """Drains pending messages from SQLite spooler and attempts to publish them."""
        if self.spooler is None:
            return 0

        pending_batch = await self.spooler.peek_batch(batch_size=max_batch)
        if not pending_batch:
            return 0

        successfully_published_ids: list[int] = []
        for row_id, message in pending_batch:
            msg_id = await self.publish(message)
            if msg_id is not None:
                successfully_published_ids.append(row_id)
            else:
                break

        if successfully_published_ids:
            await self.spooler.delete_batch(successfully_published_ids)

        return len(successfully_published_ids)
