import json
from pathlib import Path

from typer.testing import CliRunner

from research_os.cli import app
from research_os.config import project_root
from research_os.models.brief import ResearchBrief


def test_research_brief_serializes_to_workspace_shape() -> None:
    brief = ResearchBrief.from_prompt(
        prompt="optimize a world model with code and datasets",
        domain_hint="world_model",
    )
    payload = brief.model_dump()
    assert payload["domain_hints"] == ["world_model"]
    assert payload["objective"] == "optimize"


def test_bundle_create_writes_bundle_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model with code and datasets"])
    assert intake.exit_code == 0
    brief_path = Path(intake.stdout.strip())
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", brief["id"]])
    assert bundle.exit_code == 0
    bundle_path = Path(bundle.stdout.strip())
    assert bundle_path.exists()


def test_bundle_create_accepts_intake_path() -> None:
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "find a recent world model repo with dataset and optimize it"])
    assert intake.exit_code == 0
    intake_path = intake.stdout.strip()
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake_path])
    assert bundle.exit_code == 0
    assert Path(bundle.stdout.strip()).exists()


def test_bundle_create_reports_missing_intake() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["bundle", "create", "--from-intake", "missing-record"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
