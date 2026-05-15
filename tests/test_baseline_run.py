import json
from pathlib import Path

from typer.testing import CliRunner

from research_os import cli
from research_os.cli import app
from research_os.execution.baseline import record_baseline_run
from research_os.models.repro import ReproPlan
from research_os.workspace import WorkspacePaths


def test_record_baseline_run_writes_run_record_under_workspace_runs(tmp_path) -> None:
    workspace = WorkspacePaths(tmp_path)
    workspace.ensure()
    plan = ReproPlan(
        id="plan-123",
        bundle_id="bundle-123",
        runner="local",
        checklist=["recover comparable baseline", "record metric command and baseline output"],
    )

    target = record_baseline_run(plan=plan, workspace=workspace, runner="local")

    assert target.parent == tmp_path / "workspace" / "runs"
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["repro_plan_id"] == "plan-123"
    assert payload["runner"] == "local"
    assert payload["status"] == "recorded"
    assert payload["command"] == "research-os run baseline plan-123 --runner local"
    assert payload["checklist"] == plan.checklist
    assert payload["started_at"]
    assert payload["finished_at"]


def test_run_baseline_cli_accepts_repro_plan_id_and_writes_run_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = WorkspacePaths(tmp_path)
    workspace.ensure()
    plan = ReproPlan(
        id="plan-abc",
        bundle_id="bundle-abc",
        runner="local",
        checklist=["recover comparable baseline"],
    )
    plan_path = workspace.repro_plan_dir / f"{plan.id}.json"
    plan_path.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    result = CliRunner().invoke(app, ["run", "baseline", "plan-abc", "--runner", "local"])

    assert result.exit_code == 0
    output_path = Path(result.stdout.strip())
    assert output_path.parent == tmp_path / "workspace" / "runs"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["repro_plan_id"] == "plan-abc"
    assert payload["runner"] == "local"
    assert payload["command"] == "research-os run baseline plan-abc --runner local"


def test_run_baseline_cli_accepts_bundle_id_and_creates_repro_plan(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = WorkspacePaths(tmp_path)
    workspace.ensure()
    bundle_payload = {
        "id": "bundle-abc",
        "brief_id": "brief-abc",
        "title": "World model baseline",
        "summary": "Recover a comparable baseline before ideation",
        "domain_hints": ["world_model"],
        "evidence": {"items": []},
    }
    bundle_path = workspace.bundle_dir / "bundle-abc.json"
    bundle_path.write_text(json.dumps(bundle_payload, ensure_ascii=False), encoding="utf-8")

    result = CliRunner().invoke(app, ["run", "baseline", "bundle-abc", "--runner", "local"])

    assert result.exit_code == 0
    output_path = Path(result.stdout.strip())
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["runner"] == "local"
    assert payload["command"].startswith("research-os run baseline ")
    assert payload["command"].endswith(" --runner local")
    plan_files = list(workspace.repro_plan_dir.glob("*.json"))
    assert len(plan_files) == 1
    plan_payload = json.loads(plan_files[0].read_text(encoding="utf-8"))
    assert plan_payload["bundle_id"] == "bundle-abc"
    assert payload["repro_plan_id"] == plan_payload["id"]
