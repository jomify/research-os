import json
from pathlib import Path

import typer

from research_os.bundle_builder.service import build_bundle
from research_os.config import project_root
from research_os.distill.service import distill_skill
from research_os.execution.baseline import execute_checklist, record_baseline_run
from research_os.ideation.service import build_branch_set, rank_branch_results, simulate_results_from_candidates
from research_os.ingest.parser import infer_domain_hints
from research_os.innovation.review import (
    build_idea_review_record,
    build_branch_set_from_review,
    complete_idea_review,
    execute_claude_idea_review,
)
from research_os.innovation.service import build_cross_paper_innovations
from research_os.models.brief import ResearchBrief
from research_os.models.branch import BranchCandidate, BranchResult
from research_os.models.bundle import PaperBundle
from research_os.models.agent_cluster import AgentClusterPlan, AgentClusterSession
from research_os.models.innovation import CrossPaperInnovationSet, IdeaReviewRecord
from research_os.models.repro import ReproPlan
from research_os.orchestration.cluster import (
    acknowledge_agent,
    build_agent_cluster_plan,
    build_agent_dispatch,
    complete_dispatch,
    execute_claude_dispatch,
    record_agent_result,
    start_agent_cluster_session,
)
from research_os.reproduce.service import build_repro_plan
from research_os.supervisor import build_redline_audit
from research_os.web_research.service import build_live_evidence, build_stub_evidence
from research_os.workspace import WorkspacePaths

app = typer.Typer(no_args_is_help=True)
bundle_app = typer.Typer(no_args_is_help=True)
cluster_app = typer.Typer(no_args_is_help=True)
distill_app = typer.Typer(no_args_is_help=True)
evidence_app = typer.Typer(no_args_is_help=True)
repro_app = typer.Typer(no_args_is_help=True)
run_app = typer.Typer(no_args_is_help=True)
redline_app = typer.Typer(no_args_is_help=True)
app.add_typer(bundle_app, name="bundle")
app.add_typer(cluster_app, name="cluster")
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


@app.command("cross-ideas")
def cross_paper_ideas(
    bundle: str,
    top_k: int = typer.Option(8, "--top-k"),
    fulltext_dir: Path | None = typer.Option(None, "--fulltext-dir"),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    bundle_path = _resolve_json_reference(bundle, workspace.bundle_dir, "Bundle")
    paper_bundle = PaperBundle.model_validate_json(bundle_path.read_text(encoding="utf-8"))
    try:
        innovation_set = build_cross_paper_innovations(
            bundle=paper_bundle,
            top_k=top_k,
            fulltext_dir=fulltext_dir,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    target = workspace.cross_idea_dir / f"{innovation_set.id}.json"
    target.write_text(json.dumps(innovation_set.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@app.command("idea-review")
def review_ideas(
    cross_ideas: str,
    proposer: str = typer.Option("codex", "--proposer"),
    reviewer: str = typer.Option("claude_code", "--reviewer"),
    execute: bool = typer.Option(False, "--execute"),
    timeout: float = typer.Option(300, "--timeout"),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    cross_path = _resolve_json_reference(cross_ideas, workspace.cross_idea_dir, "Cross-ideas record")
    innovation_set = CrossPaperInnovationSet.model_validate_json(cross_path.read_text(encoding="utf-8"))
    record = build_idea_review_record(
        innovation_set=innovation_set,
        proposer_provider=proposer,
        reviewer_provider=reviewer,
    )
    if execute and reviewer != "claude_code":
        raise typer.BadParameter("Only claude_code idea reviews support --execute in this version.")
    if execute:
        execution = execute_claude_idea_review(record, timeout=timeout)
        record = complete_idea_review(
            record=record,
            status=str(execution["status"]),
            returncode=int(execution["returncode"]),
            stdout=str(execution["stdout"]),
            stderr=str(execution["stderr"]),
        )
    target = workspace.idea_review_dir / f"{record.id}.json"
    target.write_text(json.dumps(record.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@app.command("ideas-to-branches")
def reviewed_ideas_to_branches(
    idea_review: str,
    cross_ideas: str = typer.Option(..., "--cross-ideas"),
    include_revise: bool = typer.Option(False, "--include-revise"),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    review_path = _resolve_json_reference(idea_review, workspace.idea_review_dir, "Idea review")
    cross_path = _resolve_json_reference(cross_ideas, workspace.cross_idea_dir, "Cross-ideas record")
    review = IdeaReviewRecord.model_validate_json(review_path.read_text(encoding="utf-8"))
    innovation_set = CrossPaperInnovationSet.model_validate_json(cross_path.read_text(encoding="utf-8"))
    try:
        branch_set = build_branch_set_from_review(
            innovation_set=innovation_set,
            review=review,
            include_revise=include_revise,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
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


@cluster_app.command("plan")
def plan_agent_cluster(bundle_or_plan: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    source_path = _resolve_bundle_or_plan_path(bundle_or_plan, workspace)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    plan = build_agent_cluster_plan(payload=payload, source_path=source_path)
    target = workspace.cluster_plan_dir / f"{plan.id}.json"
    target.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@cluster_app.command("start")
def start_agent_cluster(cluster_plan: str) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    plan_path = _resolve_json_reference(cluster_plan, workspace.cluster_plan_dir, "Cluster plan")
    plan = AgentClusterPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    session = start_agent_cluster_session(plan)
    target = workspace.cluster_session_dir / f"{session.id}.json"
    target.write_text(json.dumps(session.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))


@cluster_app.command("ack")
def acknowledge_cluster_agent(
    cluster_session: str,
    agent_id: str,
    note: str = typer.Option("", "--note"),
    external_ref: str = typer.Option("", "--external-ref"),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    session_path = _resolve_json_reference(cluster_session, workspace.cluster_session_dir, "Cluster session")
    session = AgentClusterSession.model_validate_json(session_path.read_text(encoding="utf-8"))
    try:
        updated = acknowledge_agent(session=session, agent_id=agent_id, note=note, external_ref=external_ref)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    session_path.write_text(json.dumps(updated.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(session_path))


@cluster_app.command("result")
def record_cluster_agent_result(
    cluster_session: str,
    agent_id: str,
    status: str = typer.Option(..., "--status"),
    summary: str = typer.Option(..., "--summary"),
    artifact: list[str] = typer.Option([], "--artifact"),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    session_path = _resolve_json_reference(cluster_session, workspace.cluster_session_dir, "Cluster session")
    session = AgentClusterSession.model_validate_json(session_path.read_text(encoding="utf-8"))
    try:
        updated = record_agent_result(
            session=session,
            agent_id=agent_id,
            status=status,
            summary=summary,
            artifacts=artifact,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    session_path.write_text(json.dumps(updated.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(session_path))


@cluster_app.command("dispatch")
def dispatch_cluster_agent(
    cluster_session: str,
    agent_id: str,
    execute: bool = typer.Option(False, "--execute", help="Execute supported provider commands after dispatch."),
    timeout: float = typer.Option(300, "--timeout", help="Execution timeout in seconds."),
) -> None:
    workspace = WorkspacePaths(project_root())
    workspace.ensure()
    session_path = _resolve_json_reference(cluster_session, workspace.cluster_session_dir, "Cluster session")
    session = AgentClusterSession.model_validate_json(session_path.read_text(encoding="utf-8"))
    plan_path = _resolve_json_reference(session.plan_id, workspace.cluster_plan_dir, "Cluster plan")
    plan = AgentClusterPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    try:
        dispatch = build_agent_dispatch(session=session, plan=plan, agent_id=agent_id)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if execute and dispatch.provider != "claude_code":
        raise typer.BadParameter("Only claude_code dispatch supports --execute in this version.")
    dispatch_path = workspace.cluster_dispatch_dir / f"{dispatch.id}.json"
    dispatch_path.write_text(json.dumps(dispatch.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        session = acknowledge_agent(
            session=session,
            agent_id=agent_id,
            note=f"Dispatch record created at {dispatch_path}",
            external_ref=dispatch.id,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if execute:
        execution = execute_claude_dispatch(dispatch, timeout=timeout)
        dispatch = complete_dispatch(
            dispatch=dispatch,
            status=str(execution["status"]),
            returncode=int(execution["returncode"]),
            stdout=str(execution["stdout"]),
            stderr=str(execution["stderr"]),
        )
        summary = dispatch.stdout or dispatch.stderr or f"claude exited with return code {dispatch.returncode}"
        session = record_agent_result(
            session=session,
            agent_id=agent_id,
            status=dispatch.status,
            summary=summary,
            artifacts=[str(dispatch_path)],
        )
        dispatch_path.write_text(json.dumps(dispatch.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    session_path.write_text(json.dumps(session.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(dispatch_path))


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
