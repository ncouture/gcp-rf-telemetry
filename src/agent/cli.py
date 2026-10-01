"""Command Line Interface for GCP RF Telemetry Collector Agent."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import uvicorn

from agent.csv_reader import CsvTelemetryReader
from agent.pipeline import TelemetryPipeline
from agent.publisher import PubSubPublisher
from agent.server import create_app
from agent.sniffle_reader import SniffleJsonReader
from agent.spooler import SqliteSpooler


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="GCP RF Telemetry Collector Agent CLI"
    )
    parser.add_argument(
        "--csv-file",
        type=str,
        default=None,
        help="Path to RF telemetry CSV file (default: data/sample_rf.csv if no input source given)",
    )
    parser.add_argument(
        "--sniffle-json",
        type=str,
        default=None,
        help="Path to Sniffle BLE JSON capture file",
    )
    parser.add_argument(
        "--min-rssi",
        type=int,
        default=None,
        help="Minimum RSSI threshold in dBm for BLE packets",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Replay BLE capture in real-time according to packet timestamps",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=os.getenv("GCP_PROJECT_ID", "gcp-rf-telemetry"),
        help="GCP Project ID",
    )
    parser.add_argument(
        "--topic-id",
        type=str,
        default=os.getenv("PUBSUB_TOPIC_ID", "rf-telemetry-stream"),
        help="GCP Pub/Sub Topic ID",
    )
    parser.add_argument(
        "--ble-topic-id",
        type=str,
        default=os.getenv("BLE_PUBSUB_TOPIC_ID", None),
        help="Dedicated GCP Pub/Sub Topic ID for BLE scans",
    )
    parser.add_argument(
        "--spool-db",
        type=str,
        default="telemetry_spool.db",
        help="Path to SQLite offline buffer DB file",
    )
    parser.add_argument(
        "--mock-mode",
        action="store_true",
        default=True,
        help="Run GCP Pub/Sub publisher in mock mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: parse data and print summary without publishing",
    )
    parser.add_argument(
        "--loop-csv",
        action="store_true",
        help="Continuously loop data file emission",
    )
    parser.add_argument(
        "--interval-sec",
        type=float,
        default=1.0,
        help="Interval in seconds between telemetry readings",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="HTTP port for observability server (/healthz, /metrics)",
    )
    return parser.parse_args(args)


async def main_async(args):
    # Determine input source
    if args.sniffle_json:
        source_path = Path(args.sniffle_json)
        if not source_path.exists():
            print(f"Error: Sniffle JSON file not found at {source_path}")
            sys.exit(1)
        print(f"Starting GCP RF Telemetry Agent with Sniffle BLE JSON ({source_path})")
        reader = SniffleJsonReader(
            json_path=source_path,
            min_rssi=args.min_rssi,
            realtime=args.realtime,
            interval_sec=args.interval_sec if not args.realtime else 0.0,
            loop=args.loop_csv,
        )
    else:
        csv_file = args.csv_file or "data/sample_rf.csv"
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"Error: CSV file not found at {csv_path}")
            sys.exit(1)
        print(f"Starting GCP RF Telemetry Agent with Spectral CSV ({csv_path})")
        reader = CsvTelemetryReader(
            csv_path=csv_path,
            loop=args.loop_csv,
            interval_sec=args.interval_sec,
        )

    if args.dry_run:
        print("Dry run mode enabled. Reading telemetry...")
        count = 0
        async for msg in reader.read_telemetry():
            if hasattr(msg, "db_bins"):
                print(
                    f"Read spectral message: device={msg.device_id}, "
                    f"timestamp={msg.timestamp_iso}, bins={len(msg.db_bins)}"
                )
            else:
                print(
                    f"Read BLE packet: device={msg.device_id}, mac={msg.advertiser_mac}, "
                    f"pdu={msg.pdu_type}, rssi={msg.signal_dbm} dBm"
                )
            count += 1
            if count >= 10 and not args.sniffle_json:
                break
        print(f"Dry run complete. Total messages read: {count}")
        return

    spooler = SqliteSpooler(db_path=args.spool_db)
    await spooler.initialize()

    publisher = PubSubPublisher(
        project_id=args.project_id,
        topic_id=args.topic_id,
        ble_topic_id=args.ble_topic_id,
        mock_mode=args.mock_mode,
        spooler=spooler,
    )
    await publisher.initialize()

    pipeline = TelemetryPipeline(reader=reader, publisher=publisher, spooler=spooler)

    # Start FastAPI server in background
    app = create_app()
    config = uvicorn.Config(app=app, host="0.0.0.0", port=args.port, log_level="info")
    server = uvicorn.Server(config)

    server_task = asyncio.create_task(server.serve())
    pipeline_task = asyncio.create_task(
        pipeline.run_forever(poll_interval_sec=args.interval_sec)
    )

    try:
        await asyncio.gather(server_task, pipeline_task)
    finally:
        await spooler.close()


def main():
    args = parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
