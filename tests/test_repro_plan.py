import json
from pathlib import Path

from typer.testing import CliRunner

from research_os.cli import app


def test_repro_plan_from_bundle_records_baseline_gate() -> None:
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with dataset"])
    assert intake.exit_code == 0
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    assert bundle.exit_code == 0

    plan = runner.invoke(app, ["repro", "plan", bundle.stdout.strip(), "--runner", "local"])
    assert plan.exit_code == 0

    payload = json.loads(Path(plan.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["bundle_id"]
    assert payload["runner"] == "local"
    assert payload["status"] == "planned"
    assert payload["baseline_required"] is True
    assert "recover comparable baseline" in payload["checklist"]
