import json
from pathlib import Path

from typer.testing import CliRunner

from research_os.cli import app


def test_evidence_create_writes_primary_source_query_ledger() -> None:
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "find recent diffusion world model papers with github repos and datasets"])
    assert intake.exit_code == 0
    evidence = runner.invoke(app, ["evidence", "create", "--from-intake", intake.stdout.strip()])
    assert evidence.exit_code == 0

    ledger = json.loads(Path(evidence.stdout.strip()).read_text(encoding="utf-8"))
    source_types = {item["source_type"] for item in ledger["items"]}
    assert source_types == {"paper", "code", "dataset", "benchmark"}
    assert all(item["url"].startswith("query://") for item in ledger["items"])
