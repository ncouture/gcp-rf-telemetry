"""Streaming Reader for Sniffle BLE Packet JSON Captures."""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent.proto.telemetry_pb2 import BleAdvertisementMessage

PDU_TYPE_MAP = {
    "0x00": "ADV_IND",
    "0x01": "ADV_DIRECT_IND",
    "0x02": "ADV_NONCONN_IND",
    "0x03": "SCAN_REQ",
    "0x04": "SCAN_RSP",
    "0x05": "CONNECT_IND",
    "0x06": "ADV_SCAN_IND",
    "0": "ADV_IND",
    "1": "ADV_DIRECT_IND",
    "2": "ADV_NONCONN_IND",
    "3": "SCAN_REQ",
    "4": "SCAN_RSP",
    "5": "CONNECT_IND",
    "6": "ADV_SCAN_IND",
}


class SniffleJsonReader:
    """Async streaming reader for Sniffle BLE Wireshark/tshark JSON packet captures."""

    def __init__(
        self,
        json_path: str | Path,
        filter_crc_errors: bool = True,
        min_rssi: int | None = None,
        realtime: bool = False,
        interval_sec: float = 0.0,
        loop: bool = False,
        device_id_prefix: str = "sniffle",
    ) -> None:
        self.json_path = Path(json_path)
        self.filter_crc_errors = filter_crc_errors
        self.min_rssi = min_rssi
        self.realtime = realtime
        self.interval_sec = interval_sec
        self.loop = loop
        self.device_id_prefix = device_id_prefix

    def _extract_eir_entries(self, ad_data: Any) -> tuple[str, str, str]:
        """Extract device name, company ID, and service UUIDs from EIR/AD tree."""
        device_name = ""
        company_id = ""
        service_data = ""

        if not isinstance(ad_data, dict):
            return device_name, company_id, service_data

        entries = ad_data.get("btcommon.eir_ad.entry")
        if not entries:
            return device_name, company_id, service_data

        entry_list = entries if isinstance(entries, list) else [entries]
        for entry in entry_list:
            if not isinstance(entry, dict):
                continue
            if "btcommon.eir_ad.entry.device_name" in entry:
                device_name = str(entry["btcommon.eir_ad.entry.device_name"])
            if "btcommon.eir_ad.entry.company_id" in entry:
                company_id = str(entry["btcommon.eir_ad.entry.company_id"])
            if "btcommon.eir_ad.entry.service_data" in entry:
                service_data = str(entry["btcommon.eir_ad.entry.service_data"])

        return device_name, company_id, service_data

    def _parse_packet(self, packet: dict[str, Any]) -> BleAdvertisementMessage | None:
        """Parse raw Wireshark/tshark packet dict into BleAdvertisementMessage."""
        layers = packet.get("_source", {}).get("layers", {})
        if not layers:
            return None

        frame = layers.get("frame", {})
        btle_rf = layers.get("btle_rf", {})
        btle = layers.get("btle", {})

        # Check CRC validity
        crc_flags = btle_rf.get("btle_rf.flags_tree", {})
        crc_valid_raw = crc_flags.get("btle_rf.flags.crc_valid", "1")
        crc_valid = crc_valid_raw in ("1", 1, True, "true")

        if self.filter_crc_errors and not crc_valid:
            return None

        # Check RSSI threshold
        signal_dbm_str = btle_rf.get("btle_rf.signal_dbm", "0")
        try:
            signal_dbm = int(signal_dbm_str)
        except (ValueError, TypeError):
            signal_dbm = 0

        if self.min_rssi is not None and signal_dbm < self.min_rssi:
            return None

        # Channel
        channel_str = btle_rf.get("btle_rf.channel", "0")
        try:
            channel = int(channel_str)
        except (ValueError, TypeError):
            channel = 0

        # Timestamp
        time_epoch_str = frame.get("frame.time_epoch")
        if time_epoch_str:
            try:
                epoch_sec = float(time_epoch_str)
                timestamp_epoch_ms = int(epoch_sec * 1000)
                dt = datetime.fromtimestamp(epoch_sec, tz=UTC)
                timestamp_iso = dt.isoformat()
            except (ValueError, TypeError):
                dt = datetime.now(UTC)
                timestamp_iso = dt.isoformat()
                timestamp_epoch_ms = int(dt.timestamp() * 1000)
        else:
            dt = datetime.now(UTC)
            timestamp_iso = dt.isoformat()
            timestamp_epoch_ms = int(dt.timestamp() * 1000)

        # Access address
        access_address = str(
            btle.get(
                "btle.access_address",
                btle_rf.get("btle_rf.reference_access_address", ""),
            )
        )

        # PDU Type
        header_tree = btle.get("btle.advertising_header_tree", {})
        raw_pdu_type = str(header_tree.get("btle.advertising_header.pdu_type", ""))
        pdu_type = PDU_TYPE_MAP.get(raw_pdu_type, raw_pdu_type or "UNKNOWN")

        # MAC Addresses
        advertiser_mac = str(btle.get("btle.advertising_address", ""))
        scanner_mac = str(btle.get("btle.scanning_address", ""))

        # EIR / AD data extraction
        ad_tree = (
            layers.get("btcommon.eir_ad.advertising_data")
            or btle.get("btcommon.eir_ad.advertising_data")
            or btle.get("btle.scan_response_data_tree", {}).get(
                "btcommon.eir_ad.advertising_data"
            )
        )
        device_name, company_id, service_data = self._extract_eir_entries(ad_tree)

        # Device ID
        interface_name = (
            frame.get("frame.interface_id_tree", {}).get("frame.interface_name")
            or self.device_id_prefix
        )
        packet_num = frame.get("frame.number", "0")
        device_id = f"{interface_name}-node"

        # Raw scan response data
        raw_scan_resp = btle.get("btle.scan_response_data", "")
        adv_data_raw = b""
        if raw_scan_resp:
            try:
                adv_data_raw = bytes.fromhex(raw_scan_resp.replace(":", ""))
            except ValueError:
                adv_data_raw = b""

        msg = BleAdvertisementMessage(
            device_id=device_id,
            timestamp_iso=timestamp_iso,
            timestamp_epoch_ms=timestamp_epoch_ms,
            channel=channel,
            signal_dbm=signal_dbm,
            access_address=access_address,
            pdu_type=pdu_type,
            advertiser_mac=advertiser_mac,
            scanner_mac=scanner_mac,
            device_name=device_name,
            company_id=company_id,
            adv_data_raw=adv_data_raw,
            crc_valid=crc_valid,
        )
        msg.metadata["packet_number"] = str(packet_num)
        if service_data:
            msg.metadata["service_data"] = service_data

        return msg

    async def _stream_raw_objects(self) -> AsyncGenerator[dict[str, Any], None]:
        """Low-memory streaming JSON object generator for top-level array."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Sniffle JSON capture file not found: {self.json_path}")

        with open(self.json_path, encoding="utf-8") as f:  # noqa: ASYNC230
            buffer: list[str] = []
            depth = 0
            in_object = False

            for line in f:
                stripped = line.strip()
                if not in_object:
                    if stripped.startswith("{"):
                        in_object = True
                        depth = 1
                        buffer = [line]
                else:
                    buffer.append(line)
                    # Track brace depth
                    depth += line.count("{") - line.count("}")
                    if depth <= 0:
                        obj_str = "".join(buffer)
                        # Clean trailing commas
                        obj_str = obj_str.rstrip(",\r\n \t")
                        try:
                            data = json.loads(obj_str)
                            yield data
                        except (json.JSONDecodeError, ValueError):
                            pass
                        in_object = False
                        buffer = []
                        depth = 0
                await asyncio.sleep(0)

    async def read_telemetry(self) -> AsyncGenerator[BleAdvertisementMessage, None]:
        """Stream BleAdvertisementMessage objects indefinitely or until file EOF."""
        while True:
            last_epoch: float | None = None
            async for packet in self._stream_raw_objects():
                # Realtime playback delay calculation
                if self.realtime:
                    epoch_str = packet.get("_source", {}).get("layers", {}).get("frame", {}).get("frame.time_epoch")
                    if epoch_str:
                        try:
                            current_epoch = float(epoch_str)
                            if last_epoch is not None and current_epoch > last_epoch:
                                delay = min(current_epoch - last_epoch, 2.0)
                                if delay > 0:
                                    await asyncio.sleep(delay)
                            last_epoch = current_epoch
                        except ValueError:
                            pass
                elif self.interval_sec > 0.0:
                    await asyncio.sleep(self.interval_sec)

                msg = self._parse_packet(packet)
                if msg is not None:
                    yield msg

            if not self.loop:
                break
