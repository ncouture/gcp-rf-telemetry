"""Unit tests for BLE Protobuf schema serialization and TelemetryEnvelope."""

def test_ble_advertisement_message_serialization():
    from agent.proto.telemetry_pb2 import BleAdvertisementMessage

    msg = BleAdvertisementMessage(
        device_id="sniffle-node-01",
        timestamp_iso="2026-10-01T06:30:00.352756Z",
        timestamp_epoch_ms=1790836200352,
        channel=37,
        signal_dbm=-57,
        access_address="0x8e89bed6",
        pdu_type="SCAN_REQ",
        advertiser_mac="08:30:dc:4e:3d:3c",
        scanner_mac="6a:b6:b8:68:bc:d8",
        device_name="",
        company_id="",
        adv_data_raw=b"",
        crc_valid=True,
    )
    msg.metadata["packet_number"] = "1"

    serialized = msg.SerializeToString()
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0

    deserialized = BleAdvertisementMessage()
    deserialized.ParseFromString(serialized)

    assert deserialized.device_id == "sniffle-node-01"
    assert deserialized.timestamp_iso == "2026-10-01T06:30:00.352756Z"
    assert deserialized.timestamp_epoch_ms == 1790836200352
    assert deserialized.channel == 37
    assert deserialized.signal_dbm == -57
    assert deserialized.access_address == "0x8e89bed6"
    assert deserialized.pdu_type == "SCAN_REQ"
    assert deserialized.advertiser_mac == "08:30:dc:4e:3d:3c"
    assert deserialized.scanner_mac == "6a:b6:b8:68:bc:d8"
    assert deserialized.crc_valid is True
    assert deserialized.metadata["packet_number"] == "1"


def test_telemetry_envelope_polymorphism():
    from agent.proto.telemetry_pb2 import (
        BleAdvertisementMessage,
        RfTelemetryMessage,
        TelemetryEnvelope,
    )

    # Test envelope with BLE payload
    ble_msg = BleAdvertisementMessage(
        device_id="sniffle-01",
        advertiser_mac="aa:bb:cc:dd:ee:ff",
        signal_dbm=-45,
    )
    envelope_ble = TelemetryEnvelope(ble_advertisement=ble_msg)

    serialized_ble = envelope_ble.SerializeToString()
    deserialized_ble = TelemetryEnvelope()
    deserialized_ble.ParseFromString(serialized_ble)

    assert deserialized_ble.WhichOneof("payload") == "ble_advertisement"
    assert deserialized_ble.ble_advertisement.advertiser_mac == "aa:bb:cc:dd:ee:ff"
    assert deserialized_ble.ble_advertisement.signal_dbm == -45

    # Test envelope with RF spectral sweep payload
    rf_msg = RfTelemetryMessage(
        device_id="hackrf-01",
        hz_low=100.0,
        hz_high=200.0,
        db_bins=[-50.0, -48.0],
    )
    envelope_rf = TelemetryEnvelope(spectral_sweep=rf_msg)

    serialized_rf = envelope_rf.SerializeToString()
    deserialized_rf = TelemetryEnvelope()
    deserialized_rf.ParseFromString(serialized_rf)

    assert deserialized_rf.WhichOneof("payload") == "spectral_sweep"
    assert deserialized_rf.spectral_sweep.device_id == "hackrf-01"
    assert list(deserialized_rf.spectral_sweep.db_bins) == [-50.0, -48.0]
