"""Unit tests for agent CLI module."""

import pytest
from pathlib import Path

from agent.cli import parse_args, main_async


def test_cli_parse_args():
    args = parse_args(["--csv-file", "data/sample_rf.csv", "--dry-run", "--port", "9090"])
    assert args.csv_file == "data/sample_rf.csv"
    assert args.dry_run is True
    assert args.port == 9090


@pytest.mark.asyncio
async def test_cli_dry_run_execution(capsys):
    csv_path = Path(__file__).parent / "fixtures" / "sample_rf.csv"
    args = parse_args(["--csv-file", str(csv_path), "--dry-run"])

    await main_async(args)

    captured = capsys.readouterr()
    assert "Dry run complete. Total messages read: 2" in captured.out
