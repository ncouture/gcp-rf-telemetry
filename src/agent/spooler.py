"""Async SQLite Persistent Spooler for Telemetry Payloads."""

import asyncio
from pathlib import Path

import aiosqlite
from google.protobuf.message import DecodeError

from agent.proto.telemetry_pb2 import (
    BleAdvertisementMessage,
    RfTelemetryMessage,
    TelemetryEnvelope,
)


class SqliteSpooler:
    """Persistent disk-backed SQLite queue for telemetry message buffering."""

    def __init__(self, db_path: str | Path = "telemetry_spool.db") -> None:
        self.db_path = Path(db_path)
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initializes the database connection and creates table if missing."""
        async with self._lock:
            if self._conn is None:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self._conn = await aiosqlite.connect(self.db_path)
                await self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS telemetry_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payload BLOB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
                await self._conn.commit()

    async def enqueue(
        self,
        message: RfTelemetryMessage | BleAdvertisementMessage | TelemetryEnvelope,
    ) -> int:
        """Serializes and enqueues a telemetry message or envelope to disk spool."""
        if self._conn is None:
            await self.initialize()

        if isinstance(message, TelemetryEnvelope):
            envelope = message
        elif isinstance(message, BleAdvertisementMessage):
            envelope = TelemetryEnvelope(ble_advertisement=message)
        else:
            envelope = TelemetryEnvelope(spectral_sweep=message)

        payload = envelope.SerializeToString()
        async with self._lock:
            cursor = await self._conn.execute(
                "INSERT INTO telemetry_queue (payload) VALUES (?);", (payload,)
            )
            await self._conn.commit()
            return cursor.lastrowid or 0

    async def peek_batch(
        self, batch_size: int = 100
    ) -> list[tuple[int, RfTelemetryMessage | BleAdvertisementMessage]]:
        """Peeks up to batch_size oldest messages without deleting them."""
        if self._conn is None:
            await self.initialize()

        async with self._lock, self._conn.execute(
            "SELECT id, payload FROM telemetry_queue ORDER BY id ASC LIMIT ?;",
            (batch_size,),
        ) as cursor:
            rows = await cursor.fetchall()

        results: list[tuple[int, RfTelemetryMessage | BleAdvertisementMessage]] = []
        for row_id, payload in rows:
            envelope = TelemetryEnvelope()
            try:
                envelope.ParseFromString(payload)
                payload_type = envelope.WhichOneof("payload")
                if payload_type == "ble_advertisement":
                    results.append((row_id, envelope.ble_advertisement))
                    continue
                if payload_type == "spectral_sweep":
                    results.append((row_id, envelope.spectral_sweep))
                    continue
            except DecodeError:
                pass

            # Fallback for legacy raw RfTelemetryMessage payloads in existing databases
            try:
                legacy_msg = RfTelemetryMessage()
                legacy_msg.ParseFromString(payload)
                results.append((row_id, legacy_msg))
            except DecodeError:
                pass

        return results

    async def delete_batch(self, ids: list[int]) -> None:
        """Deletes processed message IDs from the spool database."""
        if not ids:
            return
        if self._conn is None:
            await self.initialize()

        placeholders = ",".join("?" for _ in ids)
        async with self._lock:
            await self._conn.execute(
                f"DELETE FROM telemetry_queue WHERE id IN ({placeholders});", ids
            )
            await self._conn.commit()

    async def get_queue_size(self) -> int:
        """Returns total count of pending messages in the spool queue."""
        if self._conn is None:
            await self.initialize()

        async with self._lock, self._conn.execute(
            "SELECT COUNT(*) FROM telemetry_queue;"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def close(self) -> None:
        """Closes the database connection."""
        async with self._lock:
            if self._conn is not None:
                await self._conn.close()
                self._conn = None
