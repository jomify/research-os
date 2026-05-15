import json
from pathlib import Path

from typer.testing import CliRunner

from research_os.cli import app


def test_ideate_writes_branch_candidates_for_all_families(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("research_os.cli.project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with dataset"])
    assert intake.exit_code == 0
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    assert bundle.exit_code == 0

    result = runner.invoke(app, ["ideate", bundle.stdout.strip()])

    assert result.exit_code == 0
    payload = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["parent_bundle_id"]
    assert [candidate["family"] for candidate in payload["candidates"]] == [
        "hyperparameter",
        "training_strategy",
        "architecture",
        "data",
        "inference",
        "paper_transfer",
    ]
    assert all(candidate["parent_bundle_id"] == payload["parent_bundle_id"] for candidate in payload["candidates"])


def test_rank_orders_branch_results_by_gain_then_cost_and_complexity(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("research_os.cli.project_root", lambda: tmp_path)
    runner = CliRunner()
    branch_file = tmp_path / "workspace" / "branches" / "manual-results.json"
    branch_file.parent.mkdir(parents=True, exist_ok=True)
    branch_file.write_text(
        json.dumps(
            {
                "parent_bundle_id": "bundle-1",
                "results": [
                    {
                        "candidate_id": "expensive",
                        "family": "architecture",
                        "metric_improvement": 0.04,
                        "resource_cost": 8.0,
                        "complexity": 7,
                    },
                    {
                        "candidate_id": "efficient",
                        "family": "hyperparameter",
                        "metric_improvement": 0.04,
                        "resource_cost": 2.0,
                        "complexity": 2,
                    },
                    {
                        "candidate_id": "weak",
                        "family": "inference",
                        "metric_improvement": 0.01,
                        "resource_cost": 1.0,
                        "complexity": 1,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["rank", str(branch_file)])

    assert result.exit_code == 0
    payload = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert [item["candidate_id"] for item in payload["items"]] == ["efficient", "expensive", "weak"]
    assert payload["items"][0]["rank"] == 1
    assert payload["items"][0]["score"] > payload["items"][1]["score"] > payload["items"][2]["score"]
