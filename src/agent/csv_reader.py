"""Async CSV Mock Telemetry Reader."""

import asyncio
import csv
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

from agent.proto.telemetry_pb2 import RfTelemetryMessage


class CsvTelemetryReader:
    """Reads spectral RF telemetry data from a CSV file and yields Protobuf messages."""

    def __init__(
        self,
        csv_path: str | Path,
        device_id: str = "edge-rf-sensor-01",
        loop: bool = False,
        interval_sec: float = 1.0,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.device_id = device_id
        self.loop = loop
        self.interval_sec = interval_sec

    def parse_row_tokens(self, header: list[str], row: list[str]) -> RfTelemetryMessage | None:
        """Parses a header and row list into an RfTelemetryMessage."""
        if not header or not row:
            return None

        # Build column index lookup
        row_map: dict[str, list[str]] = {}
        for idx, col_name in enumerate(header):
            col_key = col_name.strip()
            if col_key not in row_map:
                row_map[col_key] = []
            if idx < len(row):
                row_map[col_key].append(row[idx].strip())

        try:
            date_str = row_map.get("date", [""])[0]
            time_str = row_map.get("time", [""])[0]

            if date_str and time_str:
                dt_str = f"{date_str}T{time_str}Z"
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=UTC
                )
                epoch_ms = int(dt.timestamp() * 1000)
            else:
                now = datetime.now(UTC)
                dt_str = now.isoformat()
                epoch_ms = int(now.timestamp() * 1000)

            hz_low = float(row_map.get("hz_low", ["0.0"])[0])
            hz_high = float(row_map.get("hz_high", ["0.0"])[0])
            hz_bin_width = float(row_map.get("hz_bin_width", ["0.0"])[0])
            num_samples = int(row_map.get("num_samples", ["0"])[0])

            # Extract dB power values from all columns labeled "dB" or starting with "db"
            db_bins: list[float] = []
            for col_key, val_list in row_map.items():
                if col_key.lower().startswith("db"):
                    for val in val_list:
                        if val != "":
                            try:
                                db_bins.append(float(val))
                            except ValueError:
                                pass

            # Also check remaining unmapped trailing columns if db_bins empty
            if not db_bins:
                for idx in range(6, len(row)):
                    try:
                        db_bins.append(float(row[idx].strip()))
                    except ValueError:
                        pass

            return RfTelemetryMessage(
                device_id=self.device_id,
                timestamp_iso=dt_str,
                timestamp_epoch_ms=epoch_ms,
                hz_low=hz_low,
                hz_high=hz_high,
                hz_bin_width=hz_bin_width,
                num_samples=num_samples,
                db_bins=db_bins,
            )
        except (ValueError, KeyError, TypeError, OSError) as e:
            print(f"Error parsing CSV row: {e}")
            return None

    async def read_telemetry(self) -> AsyncGenerator[RfTelemetryMessage, None]:
        """Asynchronously streams RfTelemetryMessage objects from the CSV file."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        while True:
            with open(self.csv_path, mode="r", encoding="utf-8") as f:  # noqa: ASYNC230
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    break

                for row in reader:
                    if not row or not any(row):
                        continue
                    msg = self.parse_row_tokens(header, row)
                    if msg is not None:
                        yield msg
                        if self.interval_sec > 0:
                            await asyncio.sleep(self.interval_sec)

            if not self.loop:
                break
