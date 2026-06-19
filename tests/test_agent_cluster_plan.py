import json
from pathlib import Path

from typer.testing import CliRunner

from research_os import cli
from research_os.cli import app
from research_os.models.agent_cluster import AgentClusterPlan
from research_os.orchestration.cluster import build_agent_cluster_plan, build_agent_dispatch


def test_cluster_plan_from_bundle_assigns_codex_claude_runner_and_verifier(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with code and dataset"])
    assert intake.exit_code == 0
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    assert bundle.exit_code == 0

    result = runner.invoke(app, ["cluster", "plan", bundle.stdout.strip()])

    assert result.exit_code == 0
    payload = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert payload["source_type"] == "bundle"
    assert payload["coordinator"] == "codex"
    providers = {agent["provider"] for agent in payload["agents"]}
    assert {"codex", "claude_code", "runner", "verifier"} <= providers
    assert any("baseline" in gate.lower() for gate in payload["redline_gates"])
    assert any(handoff["target_provider"] == "claude_code" for handoff in payload["handoffs"])
    assert any(handoff["target_provider"] == "codex" for handoff in payload["handoffs"])


def test_cluster_plan_from_repro_plan_keeps_baseline_gate(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a generative baseline with code and dataset"])
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    repro = runner.invoke(app, ["repro", "plan", bundle.stdout.strip(), "--runner", "local"])
    assert repro.exit_code == 0

    result = runner.invoke(app, ["cluster", "plan", repro.stdout.strip()])

    assert result.exit_code == 0
    payload = AgentClusterPlan.model_validate_json(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert payload.source_type == "repro_plan"
    assert "recover comparable baseline" in " ".join(payload.redline_gates).lower()
    runner_agent = next(agent for agent in payload.agents if agent.provider == "runner")
    assert runner_agent.depends_on


def test_claude_handoff_prompt_is_plan_mode_and_non_secret() -> None:
    payload = {
        "id": "bundle-1",
        "title": "World model baseline",
        "summary": "Optimize after reproduction",
        "domain_hints": ["world_model"],
        "evidence": {"items": []},
    }

    plan = build_agent_cluster_plan(payload=payload, source_path=Path("bundle-1.json"))

    claude_handoff = next(handoff for handoff in plan.handoffs if handoff.target_provider == "claude_code")
    assert "claude -p" in claude_handoff.command
    assert "--permission-mode plan" in claude_handoff.command
    assert "Do not request secrets" in claude_handoff.prompt
    assert "baseline" in claude_handoff.prompt.lower()


def test_claude_handoff_command_does_not_inline_user_controlled_prompt_text() -> None:
    payload = {
        "id": "bundle-1",
        "title": 'World model "$(Write-Error injected)"',
        "summary": "Optimize after reproduction",
        "domain_hints": ["world_model"],
        "evidence": {"items": []},
    }

    plan = build_agent_cluster_plan(payload=payload, source_path=Path("bundle-1.json"))

    claude_handoff = next(handoff for handoff in plan.handoffs if handoff.target_provider == "claude_code")
    assert "$(Write-Error injected)" in claude_handoff.prompt
    assert "$(Write-Error injected)" not in claude_handoff.command


def test_cluster_start_creates_dependency_gated_session(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with code and dataset"])
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    plan = runner.invoke(app, ["cluster", "plan", bundle.stdout.strip()])
    assert plan.exit_code == 0

    result = runner.invoke(app, ["cluster", "start", plan.stdout.strip()])

    assert result.exit_code == 0
    session = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert session["plan_id"]
    assert session["status"] == "active"
    by_agent = {state["agent_id"]: state for state in session["agent_states"]}
    assert by_agent["codex-coordinator"]["status"] == "ready"
    assert by_agent["claude-literature-reviewer"]["status"] == "blocked"
    assert by_agent["baseline-runner"]["depends_on"] == ["codex-coordinator", "claude-literature-reviewer"]


def test_cluster_ack_and_result_advance_dependent_agents(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with code and dataset"])
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    plan = runner.invoke(app, ["cluster", "plan", bundle.stdout.strip()])
    session = runner.invoke(app, ["cluster", "start", plan.stdout.strip()])
    session_path = session.stdout.strip()

    ack = runner.invoke(
        app,
        [
            "cluster",
            "ack",
            session_path,
            "codex-coordinator",
            "--note",
            "Coordinator accepted",
            "--external-ref",
            "codex-thread-1",
        ],
    )
    assert ack.exit_code == 0
    acknowledged = json.loads(Path(ack.stdout.strip()).read_text(encoding="utf-8"))
    codex_state = next(state for state in acknowledged["agent_states"] if state["agent_id"] == "codex-coordinator")
    assert codex_state["status"] == "acknowledged"
    assert codex_state["external_ref"] == "codex-thread-1"

    result = runner.invoke(
        app,
        [
            "cluster",
            "result",
            session_path,
            "codex-coordinator",
            "--status",
            "completed",
            "--summary",
            "Task graph ready",
            "--artifact",
            "workspace/cluster_plans/example.json",
        ],
    )
    assert result.exit_code == 0
    updated = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    by_agent = {state["agent_id"]: state for state in updated["agent_states"]}
    assert by_agent["codex-coordinator"]["status"] == "completed"
    assert by_agent["codex-coordinator"]["artifacts"] == ["workspace/cluster_plans/example.json"]
    assert by_agent["claude-literature-reviewer"]["status"] == "ready"


def test_cluster_ack_rejects_blocked_agent_until_dependencies_complete(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with code and dataset"])
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    plan = runner.invoke(app, ["cluster", "plan", bundle.stdout.strip()])
    session = runner.invoke(app, ["cluster", "start", plan.stdout.strip()])

    blocked_ack = runner.invoke(app, ["cluster", "ack", session.stdout.strip(), "claude-literature-reviewer"])

    assert blocked_ack.exit_code != 0
    assert "blocked" in blocked_ack.output.lower()


def test_cluster_dispatch_writes_prompt_envelope_and_acknowledges_ready_agent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with code and dataset"])
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    plan = runner.invoke(app, ["cluster", "plan", bundle.stdout.strip()])
    session = runner.invoke(app, ["cluster", "start", plan.stdout.strip()])

    result = runner.invoke(app, ["cluster", "dispatch", session.stdout.strip(), "codex-coordinator"])

    assert result.exit_code == 0
    dispatch = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert dispatch["agent_id"] == "codex-coordinator"
    assert dispatch["provider"] == "codex"
    assert dispatch["status"] == "created"
    assert "Do not request secrets" in dispatch["prompt"]
    assert "prompt" not in dispatch["command"].lower()

    updated_session = json.loads(Path(session.stdout.strip()).read_text(encoding="utf-8"))
    codex_state = next(state for state in updated_session["agent_states"] if state["agent_id"] == "codex-coordinator")
    assert codex_state["status"] == "acknowledged"
    assert codex_state["external_ref"] == dispatch["id"]


def test_build_dispatch_rejects_blocked_agent() -> None:
    payload = {
        "id": "bundle-1",
        "title": "World model baseline",
        "summary": "Optimize after reproduction",
        "domain_hints": ["world_model"],
        "evidence": {"items": []},
    }
    plan = build_agent_cluster_plan(payload=payload, source_path=Path("bundle-1.json"))
    session = cli.start_agent_cluster_session(plan)

    try:
        build_agent_dispatch(session=session, plan=plan, agent_id="claude-literature-reviewer")
    except ValueError as exc:
        assert "not ready" in str(exc).lower()
    else:
        raise AssertionError("blocked agent dispatch should fail")


def test_cluster_dispatch_execute_claude_records_result_without_shell(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "project_root", lambda: tmp_path)

    calls: list[dict] = []

    def fake_execute_claude_dispatch(dispatch, timeout):
        calls.append({"command_args": dispatch.command_args, "timeout": timeout})
        return {
            "status": "completed",
            "returncode": 0,
            "stdout": "review complete",
            "stderr": "",
        }

    monkeypatch.setattr(cli, "execute_claude_dispatch", fake_execute_claude_dispatch)
    runner = CliRunner()
    intake = runner.invoke(app, ["intake", "optimize a world model repo with code and dataset"])
    bundle = runner.invoke(app, ["bundle", "create", "--from-intake", intake.stdout.strip()])
    plan = runner.invoke(app, ["cluster", "plan", bundle.stdout.strip()])
    session = runner.invoke(app, ["cluster", "start", plan.stdout.strip()])
    runner.invoke(
        app,
        [
            "cluster",
            "result",
            session.stdout.strip(),
            "codex-coordinator",
            "--status",
            "completed",
            "--summary",
            "task graph ready",
        ],
    )

    result = runner.invoke(
        app,
        ["cluster", "dispatch", session.stdout.strip(), "claude-literature-reviewer", "--execute"],
    )

    assert result.exit_code == 0
    dispatch = json.loads(Path(result.stdout.strip()).read_text(encoding="utf-8"))
    assert dispatch["status"] == "completed"
    assert dispatch["stdout"] == "review complete"
    assert calls
    assert calls[0]["command_args"][:2] == ["claude", "-p"]
    assert "--permission-mode" in calls[0]["command_args"]
    assert "plan" in calls[0]["command_args"]

    updated_session = json.loads(Path(session.stdout.strip()).read_text(encoding="utf-8"))
    claude_state = next(
        state for state in updated_session["agent_states"] if state["agent_id"] == "claude-literature-reviewer"
    )
    assert claude_state["status"] == "completed"
    assert claude_state["result_summary"] == "review complete"
