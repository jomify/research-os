from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any

from research_os.models.agent_cluster import (
    AgentAssignment,
    AgentClusterPlan,
    AgentClusterSession,
    AgentDispatchRecord,
    AgentHandoff,
    AgentSessionState,
)


def build_agent_cluster_plan(payload: dict[str, Any], source_path: Path) -> AgentClusterPlan:
    source_type = _source_type(payload)
    source_id = str(payload.get("id") or source_path.stem)
    objective = _objective(payload)
    title = str(payload.get("title") or payload.get("bundle_id") or source_id)
    domains = _domains(payload)
    agents = _assign_agents(source_type=source_type, source_id=source_id)
    return AgentClusterPlan(
        source_id=source_id,
        source_type=source_type,
        objective=objective,
        agents=agents,
        handoffs=_build_handoffs(title=title, objective=objective, domains=domains, source_path=source_path),
        execution_order=[agent.id for agent in agents],
        redline_gates=_redline_gates(source_type),
    )


def start_agent_cluster_session(plan: AgentClusterPlan) -> AgentClusterSession:
    states = [
        AgentSessionState(
            agent_id=agent.id,
            provider=agent.provider,
            depends_on=agent.depends_on,
            status="blocked" if agent.depends_on else "ready",
        )
        for agent in plan.agents
    ]
    return AgentClusterSession(plan_id=plan.id, source_id=plan.source_id, agent_states=states)


def acknowledge_agent(
    session: AgentClusterSession,
    agent_id: str,
    note: str = "",
    external_ref: str = "",
) -> AgentClusterSession:
    state = _find_state(session, agent_id)
    if state.status == "blocked":
        raise ValueError(f"Agent '{agent_id}' is blocked until dependencies complete.")
    if state.status in ("completed", "failed"):
        raise ValueError(f"Agent '{agent_id}' already has terminal status '{state.status}'.")
    state.status = "acknowledged"
    state.acknowledged_at = _now()
    state.updated_at = state.acknowledged_at
    if note:
        state.notes.append(note)
    if external_ref:
        state.external_ref = external_ref
    session.updated_at = state.updated_at
    return _refresh_session(session)


def record_agent_result(
    session: AgentClusterSession,
    agent_id: str,
    status: str,
    summary: str,
    artifacts: list[str] | None = None,
) -> AgentClusterSession:
    if status not in ("completed", "failed"):
        raise ValueError("Result status must be 'completed' or 'failed'.")
    state = _find_state(session, agent_id)
    if state.status == "blocked":
        raise ValueError(f"Agent '{agent_id}' is blocked until dependencies complete.")
    state.status = status
    state.result_summary = summary
    if artifacts:
        state.artifacts.extend(artifacts)
    state.updated_at = _now()
    session.updated_at = state.updated_at
    return _refresh_session(session)


def build_agent_dispatch(
    session: AgentClusterSession,
    plan: AgentClusterPlan,
    agent_id: str,
) -> AgentDispatchRecord:
    state = _find_state(session, agent_id)
    if state.status != "ready":
        raise ValueError(f"Agent '{agent_id}' is not ready for dispatch; current status is '{state.status}'.")
    assignment = _find_assignment(plan, agent_id)
    handoff = _handoff_for_provider(plan, assignment.provider)
    prompt = _dispatch_prompt(plan=plan, assignment=assignment, handoff=handoff)
    command, command_args = _dispatch_command(provider=assignment.provider, prompt=prompt)
    return AgentDispatchRecord(
        session_id=session.id,
        plan_id=plan.id,
        agent_id=agent_id,
        provider=assignment.provider,
        title=handoff.title if handoff else assignment.role,
        prompt=prompt,
        command=command,
        command_args=command_args,
    )


def complete_dispatch(
    dispatch: AgentDispatchRecord,
    status: str,
    returncode: int | None,
    stdout: str,
    stderr: str,
) -> AgentDispatchRecord:
    if status not in ("completed", "failed"):
        raise ValueError("Dispatch status must be 'completed' or 'failed'.")
    dispatch.status = status
    dispatch.returncode = returncode
    dispatch.stdout = stdout
    dispatch.stderr = stderr
    dispatch.updated_at = _now()
    return dispatch


def execute_claude_dispatch(dispatch: AgentDispatchRecord, timeout: float = 300) -> dict[str, str | int]:
    if dispatch.provider != "claude_code":
        raise ValueError("Only claude_code dispatch records can be executed by this helper.")
    try:
        result = subprocess.run(
            dispatch.command_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "failed", "returncode": -1, "stdout": "", "stderr": "Timeout"}
    except OSError as exc:
        return {"status": "failed", "returncode": -1, "stdout": "", "stderr": str(exc)}
    return {
        "status": "completed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _find_state(session: AgentClusterSession, agent_id: str) -> AgentSessionState:
    for state in session.agent_states:
        if state.agent_id == agent_id:
            return state
    raise ValueError(f"Agent '{agent_id}' was not found in cluster session.")


def _find_assignment(plan: AgentClusterPlan, agent_id: str) -> AgentAssignment:
    for assignment in plan.agents:
        if assignment.id == agent_id:
            return assignment
    raise ValueError(f"Agent '{agent_id}' was not found in cluster plan.")


def _handoff_for_provider(plan: AgentClusterPlan, provider: str) -> AgentHandoff | None:
    for handoff in plan.handoffs:
        if handoff.target_provider == provider:
            return handoff
    return None


def _dispatch_prompt(
    plan: AgentClusterPlan,
    assignment: AgentAssignment,
    handoff: AgentHandoff | None,
) -> str:
    base_prompt = handoff.prompt if handoff else f"Execute role: {assignment.role}"
    return (
        f"{base_prompt}\n\n"
        f"Cluster plan id: {plan.id}\n"
        f"Agent id: {assignment.id}\n"
        f"Role: {assignment.role}\n"
        f"Responsibility: {assignment.responsibility}\n"
        f"Expected outputs: {', '.join(assignment.outputs) or 'none'}\n"
        "Do not request secrets, tokens, private credentials, or destructive permissions."
    )


def _dispatch_command(provider: str, prompt: str) -> tuple[str, list[str]]:
    if provider == "claude_code":
        return "claude -p <dispatch-json.prompt> --permission-mode plan", [
            "claude",
            "-p",
            prompt,
            "--permission-mode",
            "plan",
        ]
    if provider == "codex":
        return "codex <dispatch-json>", ["codex", "<dispatch-json>"]
    if provider == "runner":
        return "research-os run baseline <repro-plan>", ["research-os", "run", "baseline", "<repro-plan>"]
    if provider == "verifier":
        return "research-os redline audit <artifact>", ["research-os", "redline", "audit", "<artifact>"]
    return "manual dispatch", []


def _refresh_session(session: AgentClusterSession) -> AgentClusterSession:
    completed = {state.agent_id for state in session.agent_states if state.status == "completed"}
    for state in session.agent_states:
        if state.status == "blocked" and all(dep in completed for dep in state.depends_on):
            state.status = "ready"
            state.updated_at = session.updated_at
    statuses = {state.status for state in session.agent_states}
    if "failed" in statuses:
        session.status = "failed"
    elif statuses == {"completed"}:
        session.status = "completed"
    else:
        session.status = "active"
    return session


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_type(payload: dict[str, Any]) -> str:
    if "checklist" in payload and "bundle_id" in payload:
        return "repro_plan"
    if "brief_id" in payload and "evidence" in payload:
        return "bundle"
    return "json"


def _objective(payload: dict[str, Any]) -> str:
    if "summary" in payload:
        return str(payload["summary"])
    if "checklist" in payload:
        return "Recover and verify a comparable baseline before branch execution."
    return "Coordinate a research workflow from the supplied JSON artifact."


def _domains(payload: dict[str, Any]) -> str:
    hints = payload.get("domain_hints") or []
    if isinstance(hints, list) and hints:
        return ", ".join(str(hint) for hint in hints)
    return "unspecified"


def _assign_agents(source_type: str, source_id: str) -> list[AgentAssignment]:
    planning_input = f"{source_type}:{source_id}"
    return [
        AgentAssignment(
            id="codex-coordinator",
            provider="codex",
            role="research cluster lead",
            responsibility="Turn the source artifact into a staged research execution plan and own final integration.",
            inputs=[planning_input],
            outputs=["cluster state", "task graph", "final integration summary"],
        ),
        AgentAssignment(
            id="claude-literature-reviewer",
            provider="claude_code",
            role="independent reviewer",
            responsibility="Review the plan for missing evidence, weak reproduction assumptions, and unsafe shortcuts.",
            inputs=[planning_input, "evidence ledger", "reproduction checklist"],
            outputs=["review notes", "risk list", "recommended constraints"],
            depends_on=["codex-coordinator"],
        ),
        AgentAssignment(
            id="baseline-runner",
            provider="runner",
            role="baseline executor",
            responsibility="Execute the baseline checklist on the selected runner and record outputs without optimization edits.",
            inputs=["repro plan", "runner configuration"],
            outputs=["baseline run record", "metric evidence", "environment notes"],
            depends_on=["codex-coordinator", "claude-literature-reviewer"],
        ),
        AgentAssignment(
            id="redline-verifier",
            provider="verifier",
            role="scientific validity gate",
            responsibility="Audit metric, dataset, split, script, output, and constraint integrity before ranking branches.",
            inputs=["baseline run record", "branch candidates", "evidence ledger"],
            outputs=["redline audit", "go/no-go decision"],
            depends_on=["baseline-runner"],
        ),
        AgentAssignment(
            id="codex-branch-executor",
            provider="codex",
            role="branch implementation owner",
            responsibility="Implement only verifier-approved branch changes with small reversible diffs.",
            inputs=["ranked branch candidates", "redline audit"],
            outputs=["branch patch", "test evidence", "run notes"],
            depends_on=["redline-verifier"],
        ),
    ]


def _build_handoffs(title: str, objective: str, domains: str, source_path: Path) -> list[AgentHandoff]:
    claude_prompt = (
        "Review this Research OS artifact as an independent research-agent reviewer.\n"
        f"Artifact: {source_path}\n"
        f"Title: {title}\n"
        f"Objective: {objective}\n"
        f"Domains: {domains}\n"
        "Focus on reproducibility, baseline comparability, evidence gaps, and invalid shortcut risks.\n"
        "Do not request secrets, tokens, private credentials, or destructive permissions.\n"
        "Return a concise risk list and concrete constraints for the Codex coordinator."
    )
    codex_prompt = (
        "Coordinate the Research OS agent cluster from this artifact.\n"
        f"Artifact: {source_path}\n"
        "Keep baseline recovery before optimization, run redline checks before ranking, "
        "and preserve every claim as workspace JSON evidence.\n"
        "Do not request secrets, tokens, private credentials, or destructive permissions."
    )
    return [
        AgentHandoff(
            target_provider="claude_code",
            title="Claude Code research review",
            prompt=claude_prompt,
            command="claude -p <prompt-from-cluster-plan-json> --permission-mode plan",
        ),
        AgentHandoff(
            target_provider="codex",
            title="Codex cluster coordination",
            prompt=codex_prompt,
            command="research-os cluster plan <artifact>",
        ),
    ]


def _redline_gates(source_type: str) -> list[str]:
    gates = [
        "Recover comparable baseline before optimization branch execution.",
        "Verify metric, dataset, split, script, output, and constraint integrity before ranking.",
        "Reject gains from changed evaluation protocol unless marked non-comparable.",
        "Attach evidence records to paper, code, dataset, and benchmark claims.",
    ]
    if source_type == "repro_plan":
        gates.insert(1, "Execute every checklist item or mark the baseline run partial with evidence.")
    return gates
