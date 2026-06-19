import json
from pathlib import Path

from typer.testing import CliRunner

from research_os import cli
from research_os.cli import app
from research_os.models.innovation import CrossPaperInnovationSet, InnovationCandidate
from research_os.innovation.review import build_idea_review_record, build_branch_set_from_review


def _innovation_set() -> CrossPaperInnovationSet:
    return CrossPaperInnovationSet(
        id="cross-123",
        bundle_id="bundle-123",
        agent_contributions=[],
        paper_signals=[],
        idea_atoms=[],
        innovation_candidates=[
            InnovationCandidate(
                id="candidate-pass",
                title="Cross AI and math stability transfer",
                source_atom_ids=["atom-ai", "atom-math"],
                source_domains=["ai_ml", "mathematics"],
                synthesis_agent="synthesis-agent",
                hypothesis="Combine latent memory with spectral regularization.",
                mechanism="AI architecture plus mathematical stability regularizer.",
                why_compatible="Both operate on latent rollout dynamics.",
                expected_gain="Improved rollout stability.",
                risk="May over-regularize.",
                required_code_surface=["losses/", "model/"],
                redline_notes=["keep metric fixed"],
                score=0.91,
            ),
            InnovationCandidate(
                id="candidate-revise",
                title="Single-domain transfer",
                source_atom_ids=["atom-ai"],
                source_domains=["ai_ml"],
                synthesis_agent="synthesis-agent",
                hypothesis="Tune transformer memory.",
                mechanism="AI-only mechanism.",
                why_compatible="Same model.",
                expected_gain="Maybe faster.",
                risk="Not cross-domain.",
                required_code_surface=["model/"],
                redline_notes=["keep metric fixed"],
                score=0.8,
            ),
        ],
    )


def test_idea_review_record_separates_codex_proposer_and_claude_reviewer() -> None:
    record = build_idea_review_record(_innovation_set(), proposer_provider="codex", reviewer_provider="claude_code")

    assert record.proposer_provider == "codex"
    assert record.reviewer_provider == "claude_code"
    assert record.status == "created"
    assert "Proposer provider: codex" in record.prompt
    assert "Reviewer provider: claude_code" in record.prompt
    assert "Do not request secrets" in record.prompt
    assert record.command == "claude -p <idea-review-json.prompt> --permission-mode plan"
    assert record.command_args[:2] == ["claude", "-p"]
    assert "--permission-mode" in record.command_args
    findings = {finding.candidate_id: finding for finding in record.findings}
    assert findings["candidate-pass"].verdict == "pass"
    assert findings["candidate-revise"].verdict == "revise"


def test_idea_review_cli_writes_review_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = cli.WorkspacePaths(tmp_path)
    workspace.ensure()
    cross_path = workspace.cross_idea_dir / "cross-123.json"
    cross_path.write_text(json.dumps(_innovation_set().model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    result = CliRunner().invoke(app, ["idea-review", "cross-123"])

    assert result.exit_code == 0
    output_path = Path(result.stdout.strip())
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path.parent == tmp_path / "workspace" / "idea_reviews"
    assert payload["proposer_provider"] == "codex"
    assert payload["reviewer_provider"] == "claude_code"
    assert payload["findings"]


def test_idea_review_cli_execute_claude_records_stdout_without_shell(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    calls: list[dict] = []

    def fake_execute(record, timeout):
        calls.append({"command_args": record.command_args, "timeout": timeout})
        return {
            "status": "completed",
            "returncode": 0,
            "stdout": "claude reviewed ideas",
            "stderr": "",
        }

    monkeypatch.setattr(cli, "execute_claude_idea_review", fake_execute)
    workspace = cli.WorkspacePaths(tmp_path)
    workspace.ensure()
    cross_path = workspace.cross_idea_dir / "cross-123.json"
    cross_path.write_text(json.dumps(_innovation_set().model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    result = CliRunner().invoke(app, ["idea-review", "cross-123", "--execute", "--timeout", "12"])

    assert result.exit_code == 0
    payload = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["stdout"] == "claude reviewed ideas"
    assert calls
    assert calls[0]["command_args"][:2] == ["claude", "-p"]
    assert calls[0]["timeout"] == 12


def test_idea_review_cli_rejects_execute_for_non_claude_reviewer(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = cli.WorkspacePaths(tmp_path)
    workspace.ensure()
    cross_path = workspace.cross_idea_dir / "cross-123.json"
    cross_path.write_text(json.dumps(_innovation_set().model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    result = CliRunner().invoke(app, ["idea-review", "cross-123", "--reviewer", "manual", "--execute"])

    assert result.exit_code != 0
    assert "claude_code" in result.output


def test_build_branch_set_from_review_only_uses_passed_candidates() -> None:
    innovation_set = _innovation_set()
    review = build_idea_review_record(innovation_set)

    branch_set = build_branch_set_from_review(
        innovation_set=innovation_set,
        review=review,
        include_revise=False,
    )

    assert branch_set.parent_bundle_id == "bundle-123"
    assert len(branch_set.candidates) == 1
    candidate = branch_set.candidates[0]
    assert candidate.family == "paper_transfer"
    assert candidate.title == "Cross AI and math stability transfer"
    assert "Reviewed verdict: pass" in candidate.rationale
    assert "Combine latent memory with spectral regularization." in candidate.proposed_change


def test_build_branch_set_from_review_can_include_revise_candidates() -> None:
    innovation_set = _innovation_set()
    review = build_idea_review_record(innovation_set)

    branch_set = build_branch_set_from_review(
        innovation_set=innovation_set,
        review=review,
        include_revise=True,
    )

    assert len(branch_set.candidates) == 2


def test_ideas_to_branches_cli_writes_branch_set(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    workspace = cli.WorkspacePaths(tmp_path)
    workspace.ensure()
    innovation_set = _innovation_set()
    review = build_idea_review_record(innovation_set)
    cross_path = workspace.cross_idea_dir / "cross-123.json"
    review_path = workspace.idea_review_dir / "review-123.json"
    cross_path.write_text(json.dumps(innovation_set.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    review_path.write_text(json.dumps(review.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    result = CliRunner().invoke(app, ["ideas-to-branches", "review-123", "--cross-ideas", "cross-123"])

    assert result.exit_code == 0
    output_path = Path(result.stdout.strip())
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path.parent == tmp_path / "workspace" / "branches"
    assert payload["parent_bundle_id"] == "bundle-123"
    assert len(payload["candidates"]) == 1
    assert payload["candidates"][0]["family"] == "paper_transfer"
