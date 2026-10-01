"""Telemetry Data Pipeline Orchestrator."""

import asyncio
from typing import Any

from agent.publisher import PubSubPublisher
from agent.server import MESSAGES_PROCESSED_TOTAL, MESSAGES_SPOOLED_TOTAL, SPOOL_QUEUE_SIZE
from agent.spooler import SqliteSpooler


class TelemetryPipeline:
    """Orchestrates telemetry ingestion from reader, spooling, and publishing to GCP Pub/Sub."""

    def __init__(
        self,
        reader: Any,
        publisher: PubSubPublisher,
        spooler: SqliteSpooler | None = None,
    ) -> None:
        self.reader = reader
        self.publisher = publisher
        self.spooler = spooler or publisher.spooler

    async def run_once(self) -> int:
        """Processes available telemetry messages once."""
        count = 0
        async for msg in self.reader.read_telemetry():
            pub_id = await self.publisher.publish(msg)
            MESSAGES_PROCESSED_TOTAL.inc()
            count += 1

            if pub_id is None and self.spooler is not None:
                MESSAGES_SPOOLED_TOTAL.inc()

            # Attempt to drain spooler if connected
            if pub_id is not None and self.spooler is not None:
                await self.publisher.drain_spooler()

            if self.spooler is not None:
                size = await self.spooler.get_queue_size()
                SPOOL_QUEUE_SIZE.set(size)

        return count

    async def run_forever(self, poll_interval_sec: float = 1.0) -> None:
        """Continuously runs the telemetry pipeline loop."""
        while True:
            try:
                await self.run_once()
            except (RuntimeError, ValueError, OSError) as e:
                print(f"Error in telemetry pipeline loop: {e}")
            await asyncio.sleep(poll_interval_sec)
