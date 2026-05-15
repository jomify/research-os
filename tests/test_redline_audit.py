import json
from pathlib import Path

from typer.testing import CliRunner

from research_os.cli import app


def test_redline_audit_writes_integrity_report_for_repro_plan(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with dataset and metrics"])
    assert intake.exit_code == 0
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    assert bundle.exit_code == 0
    plan = runner.invoke(app, ["repro", "plan", bundle.stdout.strip(), "--runner", "local"])
    assert plan.exit_code == 0

    audit = runner.invoke(app, ["redline", "audit", plan.stdout.strip()])
    assert audit.exit_code == 0

    audit_path = Path(audit.stdout.strip())
    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit_path.parent.name == "redline_audits"
    assert payload["subject_type"] == "repro_plan"
    assert payload["subject_id"]
    assert {check["area"] for check in payload["checks"]} == {
        "metric",
        "dataset",
        "split",
        "script",
        "output",
        "constraint",
    }
    assert payload["summary"]["total"] == 6
    assert payload["summary"]["warn"] >= 1


def test_redline_audit_accepts_bundle_reference(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with dataset and metrics"])
    assert intake.exit_code == 0
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    assert bundle.exit_code == 0
    bundle_path = Path(bundle.stdout.strip())
    bundle_id = json.loads(bundle_path.read_text(encoding="utf-8"))["id"]

    audit = runner.invoke(app, ["redline", "audit", bundle_id])
    assert audit.exit_code == 0

    payload = json.loads(Path(audit.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["subject_type"] == "bundle"
    assert payload["subject_id"] == bundle_id
