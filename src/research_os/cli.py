import json
from pathlib import Path

import typer

from research_os.bundle_builder.service import build_bundle
from research_os.config import project_root
from research_os.distill.service import distill_skill
from research_os.execution.baseline import execute_checklist, record_baseline_run
from research_os.ideation.service import build_branch_set, rank_branch_results, simulate_results_from_candidates
from research_os.ingest.parser import infer_domain_hints
from research_os.models.brief import ResearchBrief
from research_os.models.branch import BranchCandidate, BranchResult
from research_os.models.bundle import PaperBundle
from research_os.models.repro import ReproPlan
from research_os.reproduce.service import build_repro_plan
from research_os.supervisor import build_redline_audit
from research_os.web_research.service import build_live_evidence, build_stub_evidence
from research_os.workspace import WorkspacePaths

app = typer.Typer(no_args_is_help=True)
bundle_app = typer.Typer(no_args_is_help=True)
distill_app = typer.Typer(no_args_is_help=True)
evidence_app = typer.Typer(no_args_is_help=True)
repro_app = typer.Typer(no_args_is_help=True)
run_app = typer.Typer(no_args_is_help=True)
redline_app = typer.Typer(no_args_is_help=True)
app.add_typer(bundle_app, name="bundle")
app.add_typer(distill_app, name="distill")
app.add_typer(evidence_app, name="evidence")
app.add_typer(repro_app, name="repro")
app.add_typer(run_app, name="run")
app.add_typer(redline_app, name="redline")


@app.command()
def intake(prompt: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    hints = infer_domain_hints(prompt)
    brief = ResearchBrief.from_prompt(prompt=prompt, domain_hints=hints)
    target = workspace.intake_dir / f"{brief.id}.json"
    target.write_text(json.dumps(brief.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


def _resolve_intake_path(reference: str, workspace: WorkspacePaths) -> Path:
    candidate = Path(reference)
    if candidate.exists():
        return candidate
    if candidate.suffix == ".json":
        stem = candidate.stem
    else:
        stem = candidate.name
    lookup = workspace.intake_dir / f"{stem}.json"
    if lookup.exists():
        return lookup
    raise typer.BadParameter(
        f"Intake record '{reference}' was not found. Pass an intake id or a path to an intake JSON file."
    )


def _resolve_json_reference(reference: str, directory: Path, label: str) -> Path:
    candidate = Path(reference)
    if candidate.exists():
        return candidate
    stem = candidate.stem if candidate.suffix == ".json" else candidate.name
    lookup = directory / f"{stem}.json"
    if lookup.exists():
        return lookup
    raise typer.BadParameter(f"{label} '{reference}' was not found. Pass an id or a path to a JSON file.")


def _resolve_bundle_or_plan_path(reference: str, workspace: WorkspacePaths) -> Path:
    candidate = Path(reference)
    if candidate.exists():
        return candidate
    stem = candidate.stem if candidate.suffix == ".json" else candidate.name
    for directory in (workspace.bundle_dir, workspace.repro_plan_dir):
        lookup = directory / f"{stem}.json"
        if lookup.exists():
            return lookup
    raise typer.BadParameter(
        f"Bundle or repro plan '{reference}' was not found. Pass an id or a path to a JSON file."
    )


@evidence_app.command("create")
def create_evidence(
    from_intake: str = typer.Option(..., "--from-intake"),
    live: bool = typer.Option(False, "--live", help="Query supported public research sources."),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    brief_path = _resolve_intake_path(from_intake, workspace)
    brief = ResearchBrief.model_validate_json(brief_path.read_text(encoding="utf-8"))
    ledger = build_live_evidence(brief) if live else build_stub_evidence(brief)
    target = workspace.evidence_dir / f"{brief.id}.json"
    target.write_text(json.dumps(ledger.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@bundle_app.command("create")
def create_bundle(
    from_intake: str = typer.Option(..., "--from-intake"),
    live: bool = typer.Option(False, "--live", help="Query supported public research sources."),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    brief_path = _resolve_intake_path(from_intake, workspace)
    brief = ResearchBrief.model_validate_json(brief_path.read_text(encoding="utf-8"))
    bundle = build_bundle(brief, live=live)
    target = workspace.bundle_dir / f"{bundle.id}.json"
    target.write_text(json.dumps(bundle.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@repro_app.command("plan")
def plan_reproduction(bundle: str, runner: str = typer.Option("local", "--runner")) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    bundle_path = _resolve_json_reference(bundle, workspace.bundle_dir, "Bundle")
    paper_bundle = PaperBundle.model_validate_json(bundle_path.read_text(encoding="utf-8"))
    plan = build_repro_plan(bundle=paper_bundle, runner=runner)
    target = workspace.repro_plan_dir / f"{plan.id}.json"
    target.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@app.command("ideate")
def ideate_bundle(bundle: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    bundle_path = _resolve_json_reference(bundle, workspace.bundle_dir, "Bundle")
    paper_bundle = PaperBundle.model_validate_json(bundle_path.read_text(encoding="utf-8"))
    branch_set = build_branch_set(paper_bundle)
    branch_dir = workspace.workspace_dir / "branches"
    branch_dir.mkdir(parents=True, exist_ok=True)
    target = branch_dir / f"{branch_set.id}.json"
    target.write_text(json.dumps(branch_set.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@app.command("rank")
def rank_branches(branch_file: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    branch_dir = workspace.workspace_dir / "branches"
    branch_path = _resolve_json_reference(branch_file, branch_dir, "Branch file")
    payload = json.loads(branch_path.read_text(encoding="utf-8"))
    results = [BranchResult.model_validate(item) for item in payload.get("results", [])]
    if not results and "candidates" in payload:
        candidates = [BranchCandidate.model_validate(c) for c in payload["candidates"]]
        results = simulate_results_from_candidates(candidates)
    ranking = rank_branch_results(parent_bundle_id=payload["parent_bundle_id"], results=results)
    ranking_dir = workspace.workspace_dir / "rankings"
    ranking_dir.mkdir(parents=True, exist_ok=True)
    target = ranking_dir / f"{ranking.id}.json"
    target.write_text(json.dumps(ranking.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@run_app.command("baseline")
def run_baseline(repro_plan: str, runner: str = typer.Option("local", "--runner")) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    source_path = _resolve_bundle_or_plan_path(repro_plan, workspace)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if "checklist" in payload:
        plan = ReproPlan.model_validate(payload)
    else:
        paper_bundle = PaperBundle.model_validate(payload)
        plan = build_repro_plan(bundle=paper_bundle, runner=runner)
        plan_path = workspace.repro_plan_dir / f"{plan.id}.json"
        plan_path.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    target = record_baseline_run(plan=plan, workspace=workspace, runner=runner)
    checklist_results = execute_checklist(plan=plan, workspace=workspace)
    run_payload = json.loads(target.read_text(encoding="utf-8"))
    run_payload["checklist_results"] = checklist_results
    run_payload["status"] = "completed" if all(r["success"] for r in checklist_results) else "partial"
    target.write_text(json.dumps(run_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@redline_app.command("audit")
def audit_redline(bundle_or_plan: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    source_path = _resolve_bundle_or_plan_path(bundle_or_plan, workspace)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    audit = build_redline_audit(source_path=source_path, payload=payload)
    target_dir = workspace.workspace_dir / "redline_audits"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{audit.id}.json"
    target.write_text(json.dumps(audit.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@distill_app.command("skill")
def distill_skill_command(run_or_bundle: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    source_path = _resolve_bundle_or_plan_path(run_or_bundle, workspace)
    record, record_path = distill_skill(source_path=source_path, workspace_dir=workspace.workspace_dir)
    typer.echo(
        json.dumps(
            {
                "record_path": str(record_path),
                "draft_path": record.draft_path,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    app()
