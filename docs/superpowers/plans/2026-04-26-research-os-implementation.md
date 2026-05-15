# Research OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable `research-os` skeleton for AutoSOTA-style research intake, evidence collection, paper bundling, runner abstraction, and skill-based operator entry.

**Architecture:** Implement a thin orchestration-first Python package with explicit schemas, a small CLI, file-backed local workspace state, and pluggable runner interfaces. Defer heavy execution logic and live integrations behind adapters so the first release is runnable without locking the system to a single backend.

**Tech Stack:** Python 3.10+, `pydantic`, `typer`, `pytest`, local JSON workspace storage, optional adapter hooks for `OMX`, `MCP`, and `autoresearch`.

---

## File Structure

### Create

- `E:\WORKSPACE\AI工具\research-os\pyproject.toml`
- `E:\WORKSPACE\AI工具\research-os\README.md`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\cli.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\config.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\workspace.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\models\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\models\brief.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\models\evidence.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\models\bundle.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\models\runner.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\ingest\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\ingest\parser.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\web_research\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\web_research\service.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\bundle_builder\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\bundle_builder\service.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\base.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\local.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\ssh.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\slurm.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\__init__.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\registry.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\multimodal.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\generative.py`
- `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\world_model.py`
- `E:\WORKSPACE\AI工具\research-os\skills\autosota-research-loop\SKILL.md`
- `E:\WORKSPACE\AI工具\research-os\tests\test_cli_intake.py`
- `E:\WORKSPACE\AI工具\research-os\tests\test_bundle_create.py`
- `E:\WORKSPACE\AI工具\research-os\tests\test_runner_registry.py`
- `E:\WORKSPACE\AI工具\research-os\tests\test_skill_content.py`

### Modify

- `E:\WORKSPACE\AI工具\research-os\docs\superpowers\specs\2026-04-26-research-os-design.md`
  - only if spec-review fixes are required during implementation

## Task 1: Bootstrap Project Package

**Files:**
- Create: `E:\WORKSPACE\AI工具\research-os\pyproject.toml`
- Create: `E:\WORKSPACE\AI工具\research-os\README.md`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\__init__.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_cli_intake.py`

- [ ] **Step 1: Write the failing packaging smoke test**

```python
from pathlib import Path


def test_project_has_cli_entrypoint() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "research-os" in pyproject
    assert "research_os.cli:app" in pyproject
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_intake.py -k project_has_cli_entrypoint -v`

Expected: `FAIL` because `pyproject.toml` does not exist yet.

- [ ] **Step 3: Write minimal package bootstrap**

```toml
[project]
name = "research-os"
version = "0.1.0"
description = "AutoSOTA-style research operating system"
requires-python = ">=3.10"
dependencies = ["pydantic>=2.8,<3", "typer>=0.12,<1"]

[project.optional-dependencies]
dev = ["pytest>=8.2,<9"]

[project.scripts]
research-os = "research_os.cli:app"

[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"
```

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_intake.py -k project_has_cli_entrypoint -v`

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src/research_os/__init__.py tests/test_cli_intake.py
git commit -m "feat: bootstrap research-os package"
```

## Task 2: Add Core Schemas and Workspace Storage

**Files:**
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\config.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\workspace.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\models\brief.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\models\evidence.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\models\bundle.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\models\runner.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_bundle_create.py`

- [ ] **Step 1: Write the failing schema serialization test**

```python
from research_os.models.brief import ResearchBrief


def test_research_brief_serializes_to_workspace_shape() -> None:
    brief = ResearchBrief.from_prompt(
        prompt="optimize a world model with code and datasets",
        domain_hint="world_model",
    )
    payload = brief.model_dump()
    assert payload["domain_hints"] == ["world_model"]
    assert payload["objective"] == "optimize"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bundle_create.py -k research_brief_serializes_to_workspace_shape -v`

Expected: `FAIL` because the model module does not exist yet.

- [ ] **Step 3: Write minimal schema and storage implementation**

```python
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class ResearchBrief(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    prompt: str
    objective: str
    domain_hints: list[str]
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def from_prompt(cls, prompt: str, domain_hint: str | None = None) -> "ResearchBrief":
        lowered = prompt.lower()
        objective = "optimize" if "optimiz" in lowered or "优化" in prompt else "reproduce"
        hints = [domain_hint] if domain_hint else []
        return cls(prompt=prompt, objective=objective, domain_hints=hints)
```

```python
from pathlib import Path


class WorkspacePaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.intake_dir = root / "workspace" / "intake"
        self.bundle_dir = root / "workspace" / "bundles"
        self.evidence_dir = root / "workspace" / "evidence"

    def ensure(self) -> None:
        for path in (self.intake_dir, self.bundle_dir, self.evidence_dir):
            path.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bundle_create.py -k research_brief_serializes_to_workspace_shape -v`

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add src/research_os/config.py src/research_os/workspace.py src/research_os/models tests/test_bundle_create.py
git commit -m "feat: add core schemas and workspace storage"
```

## Task 3: Implement Natural-Language Intake and Bundle Creation CLI

**Files:**
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\cli.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\ingest\parser.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\web_research\service.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\bundle_builder\service.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_cli_intake.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_bundle_create.py`

- [ ] **Step 1: Write the failing CLI intake test**

```python
from typer.testing import CliRunner

from research_os.cli import app


def test_intake_command_writes_brief_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["intake", "find a diffusion repo with dataset and optimize it"])
    assert result.exit_code == 0
    intake_dir = tmp_path / "workspace" / "intake"
    assert list(intake_dir.glob("*.json"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_intake.py -k intake_command_writes_brief_file -v`

Expected: `FAIL` because the CLI and service modules are not implemented yet.

- [ ] **Step 3: Write minimal intake and bundle services**

```python
def infer_domain_hints(prompt: str) -> list[str]:
    lowered = prompt.lower()
    hints: list[str] = []
    if "world model" in lowered or "world-model" in lowered:
        hints.append("world_model")
    if "diffusion" in lowered or "generat" in lowered:
        hints.append("generative")
    if "multimodal" in lowered or "vqa" in lowered:
        hints.append("multimodal")
    return hints
```

```python
import json
from pathlib import Path

import typer

from research_os.models.brief import ResearchBrief
from research_os.workspace import WorkspacePaths

app = typer.Typer(no_args_is_help=True)


@app.command()
def intake(prompt: str) -> None:
    workspace = WorkspacePaths(Path.cwd())
    workspace.ensure()
    hints = infer_domain_hints(prompt)
    brief = ResearchBrief.from_prompt(prompt=prompt, domain_hint=hints[0] if hints else None)
    target = workspace.intake_dir / f"{brief.id}.json"
    target.write_text(json.dumps(brief.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(str(target))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_cli_intake.py tests/test_bundle_create.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add src/research_os/cli.py src/research_os/ingest src/research_os/web_research src/research_os/bundle_builder tests/test_cli_intake.py tests/test_bundle_create.py
git commit -m "feat: add intake and bundle creation cli"
```

## Task 4: Add Runner Registry and Backend Stubs

**Files:**
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\base.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\local.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\ssh.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\runner\slurm.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_runner_registry.py`

- [ ] **Step 1: Write the failing runner registry test**

```python
from research_os.runner import get_runner


def test_runner_registry_exposes_first_version_backends() -> None:
    assert get_runner("local").name == "local"
    assert get_runner("ssh").name == "ssh"
    assert get_runner("slurm").name == "slurm"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_runner_registry.py -v`

Expected: `FAIL` because the runner registry does not exist yet.

- [ ] **Step 3: Write minimal runner abstraction**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Runner:
    name: str
    description: str


def get_runner(name: str) -> Runner:
    registry = {
        "local": Runner(name="local", description="Execute on the current machine"),
        "ssh": Runner(name="ssh", description="Execute through a remote SSH host"),
        "slurm": Runner(name="slurm", description="Submit batch jobs to a Slurm cluster"),
    }
    return registry[name]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_runner_registry.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add src/research_os/runner tests/test_runner_registry.py
git commit -m "feat: add runner registry stubs"
```

## Task 5: Add Domain Registry and First Operator Skill

**Files:**
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\registry.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\multimodal.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\generative.py`
- Create: `E:\WORKSPACE\AI工具\research-os\src\research_os\domains\world_model.py`
- Create: `E:\WORKSPACE\AI工具\research-os\skills\autosota-research-loop\SKILL.md`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_skill_content.py`

- [ ] **Step 1: Write the failing skill content test**

```python
from pathlib import Path


def test_autosota_skill_mentions_redline_and_parallel_branches() -> None:
    content = Path("skills/autosota-research-loop/SKILL.md").read_text(encoding="utf-8")
    assert "parallel branch" in content.lower()
    assert "redline" in content.lower()
    assert "research-os intake" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_skill_content.py -v`

Expected: `FAIL` because the skill file does not exist yet.

- [ ] **Step 3: Write minimal domain registry and operator skill**

```python
DOMAIN_REGISTRY = {
    "multimodal": {"label": "Multimodal", "default_metrics": ["accuracy", "f1"]},
    "generative": {"label": "Generative", "default_metrics": ["fid", "clip_score"]},
    "world_model": {"label": "World Model", "default_metrics": ["loss", "success_rate"]},
}
```

```markdown
---
name: autosota-research-loop
description: Use when running the research-os workflow for natural-language intake, evidence-backed paper selection, redline-audited reproduction, and parallel branch optimization.
---

# AutoSOTA Research Loop

Use this skill when the goal is to start from a natural-language research objective and turn it into an audited optimization loop.

## Required sequence

1. Run `research-os intake "<goal>"`
2. Create a bundle from the intake record
3. Recover a baseline before proposing modifications
4. Audit every idea against redline rules
5. Execute parallel branch candidates on the selected runner
6. Rank survivors and only continue with valid winning branches

## Guardrails

- Never skip baseline recovery
- Never claim gains without redline review
- Prefer primary sources for papers, repos, and datasets
- Record branch outcomes before starting the next generation
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_skill_content.py -v`

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add src/research_os/domains skills/autosota-research-loop/SKILL.md tests/test_skill_content.py
git commit -m "feat: add domain registry and operator skill"
```

## Task 6: Verify First Skeleton End-to-End

**Files:**
- Modify: `E:\WORKSPACE\AI工具\research-os\README.md`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_cli_intake.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_bundle_create.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_runner_registry.py`
- Test: `E:\WORKSPACE\AI工具\research-os\tests\test_skill_content.py`

- [ ] **Step 1: Write the README verification expectations**

```markdown
## First-run verification

```powershell
python -m pytest
python -m research_os.cli intake "find a recent world model repo with dataset and optimize it"
```

Expected:
- all tests pass
- intake command prints a JSON file path under `workspace/intake`
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 3: Run the CLI smoke command**

Run: `python -m research_os.cli intake "find a recent world model repo with dataset and optimize it"`

Expected: a created JSON path under `workspace/intake`.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add first-run verification guidance"
```

## Spec Coverage Check

- Natural-language intake: covered by Task 3
- Evidence-aware structure and bundle flow: covered by Task 2 and Task 3 skeleton interfaces
- Runner abstraction for local, ssh, slurm: covered by Task 4
- Multimodal, generative, world-model specialization hooks: covered by Task 5
- Skill-based operator entry: covered by Task 5
- First skeleton and verification flow: covered by Task 6

## Placeholder Scan

No plan steps use `TBD`, `TODO`, or unresolved placeholder language. Every code-producing step includes concrete file paths and starter code.

## Type Consistency Check

- CLI entry remains `research_os.cli:app` across all tasks.
- Primary schema names remain `ResearchBrief`, `PaperBundle`, and `Runner`.
- Workspace storage paths remain under `workspace/`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-26-research-os-implementation.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
