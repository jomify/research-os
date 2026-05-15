import json
from pathlib import Path

from typer.testing import CliRunner

from research_os import cli
from research_os.cli import app


def test_distill_skill_from_bundle_writes_memory_record_and_markdown_draft(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with dataset"])
    assert intake.exit_code == 0
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    assert bundle.exit_code == 0

    result = runner.invoke(app, ["distill", "skill", bundle.stdout.strip()])
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    record_path = Path(payload["record_path"])
    draft_path = Path(payload["draft_path"])
    record = json.loads(record_path.read_text(encoding="utf-8"))
    markdown = draft_path.read_text(encoding="utf-8")

    assert record_path.parent == tmp_path / "workspace" / "memory"
    assert draft_path.parent == tmp_path / "workspace" / "exports"
    assert record["source_id"]
    assert record["source_type"] == "bundle"
    assert "optimize a world model repo with dataset" in record["trigger"]
    assert "Never skip baseline recovery" in record["guardrails"]
    assert record["evidence_references"]
    assert record["evidence_references"][0]["source_type"]
    assert record["evidence_references"][0]["claim"]
    assert record["source_id"] in markdown
    assert "## Trigger" in markdown
    assert "## Guardrails" in markdown
    assert "## Evidence References" in markdown


def test_distill_skill_from_run_json_uses_run_command_as_trigger(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    run_path = tmp_path / "run.json"
    run_path.write_text(
        json.dumps(
            {
                "id": "run-123",
                "repro_plan_id": "plan-456",
                "runner": "local",
                "status": "recorded",
                "command": "python train.py --baseline",
                "checklist": ["recover comparable baseline"],
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["distill", "skill", str(run_path)])
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    record = json.loads(Path(payload["record_path"]).read_text(encoding="utf-8"))
    markdown = Path(payload["draft_path"]).read_text(encoding="utf-8")

    assert record["source_id"] == "run-123"
    assert record["source_type"] == "run"
    assert "python train.py --baseline" in record["trigger"]
    assert "recover comparable baseline" in record["trigger"]
    assert "python train.py --baseline" in markdown
