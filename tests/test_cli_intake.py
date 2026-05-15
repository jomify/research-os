import json
from pathlib import Path

from typer.testing import CliRunner

from research_os.cli import app
from research_os.config import project_root


def test_project_has_cli_entrypoint() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "research-os" in pyproject
    assert "research_os.cli:app" in pyproject


def test_intake_command_writes_brief_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["intake", "find a diffusion repo with dataset and optimize it"])
    assert result.exit_code == 0
    intake_dir = project_root() / "workspace" / "intake"
    assert list(intake_dir.glob("*.json"))


def test_intake_parses_chinese_prompt() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["intake", "\u4f18\u5316\u4e00\u4e2a\u4e16\u754c\u6a21\u578b\uff0c\u8981\u6c42\u4ee3\u7801\u548c\u6570\u636e\u96c6"])
    assert result.exit_code == 0
    payload = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["objective"] == "optimize"
    assert payload["domain_hints"] == ["world_model"]
    assert payload["requires_code"] is True
    assert payload["requires_datasets"] is True
