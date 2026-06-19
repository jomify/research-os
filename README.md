# Research OS

Research OS is a local-first research operating system for turning a natural-language research goal into evidence-backed tasks, reproducible baselines, audited experiment branches, and reusable research skills.

It is built for AutoSOTA-style workflows where the important question is not only "what should we try?", but also "can we reproduce the baseline, keep the comparison fair, and preserve the winning path for the next run?"

```text
goal
  -> intake
  -> evidence ledger
  -> paper bundle
  -> cross-paper innovation extraction
  -> reproduction plan
  -> baseline run
  -> branch ideation
  -> redline audit
  -> ranking
  -> skill distillation
```

## What It Does

- Converts free-form research prompts into structured local workspace records.
- Builds evidence ledgers for papers, code repositories, datasets, and benchmark protocols.
- Creates paper bundles with source claims attached to the research target.
- Extracts cross-paper idea atoms and synthesizes broad-domain innovation candidates.
- Produces baseline-first reproduction plans before optimization begins.
- Generates branch candidates across hyperparameter, training, architecture, data, inference, and paper-transfer ideas.
- Runs redline audits for metric, dataset, split, script, output, and constraint integrity.
- Ranks branch results by improvement, cost, and complexity.
- Distills successful bundles or runs into reusable skill drafts.

## Current Status

Research OS is currently a v0.1 framework skeleton. The control plane is implemented and covered by tests; heavy experiment execution is intentionally adapter-shaped so local, SSH, Slurm, and future GPU backends can be wired in without changing the research record format.

Included today:

- Typer CLI under `research-os`
- Pydantic schemas for briefs, evidence, bundles, plans, runs, branches, rankings, audits, and distilled skills
- File-backed workspace storage under `workspace/`
- Public-source adapters for arXiv, GitHub repository search, and Hugging Face dataset search
- Runner registry for `local`, `ssh`, and `slurm`
- Domain registry for `multimodal`, `generative`, and `world_model`
- Cross-paper innovation extraction across AI, core CS, mathematics, biology/neuroscience, physics, chemistry, medicine, and engineering signals
- Agent cluster planning and dependency-gated session state for Codex, Claude Code, runner, and verifier work
- Tests for the core workflow

## Installation

Research OS requires Python 3.10 or newer.

```powershell
python -m pip install -e .[dev]
```

If your shell treats extras syntax specially, quote it:

```powershell
python -m pip install -e ".[dev]"
```

## Quick Start

Create a research brief:

```powershell
$intake = research-os intake "find recent diffusion world model papers with code, datasets, and reproducible baselines"
```

Create an evidence ledger:

```powershell
$evidence = research-os evidence create --from-intake $intake --live
```

Build a paper bundle:

```powershell
$bundle = research-os bundle create --from-intake $intake --live
```

Extract cross-paper innovation candidates:

```powershell
$cross = research-os cross-ideas $bundle --top-k 8
```

Optionally pass local full-text extracts named by evidence id, such as `paper-ai.txt`, to recover
paper sections and an idea graph:

```powershell
$cross = research-os cross-ideas $bundle --top-k 8 --fulltext-dir .\paper_texts
```

Review ideas with a separate model role, for example Codex proposes and Claude Code reviews:

```powershell
$review = research-os idea-review $cross --proposer codex --reviewer claude_code
```

Claude Code review can be executed explicitly in plan mode:

```powershell
$review = research-os idea-review $cross --proposer codex --reviewer claude_code --execute
```

Convert reviewed ideas into experiment branch candidates:

```powershell
$branches = research-os ideas-to-branches $review --cross-ideas $cross
research-os rank $branches
```

Create a baseline-first reproduction plan:

```powershell
$plan = research-os repro plan $bundle --runner local
```

Record a baseline run:

```powershell
$run = research-os run baseline $plan --runner local
```

Generate and rank experiment branches:

```powershell
$branches = research-os ideate $bundle
research-os rank $branches
```

Audit the bundle or plan:

```powershell
research-os redline audit $plan
```

Create a Codex + Claude Code agent cluster plan:

```powershell
$cluster = research-os cluster plan $plan
```

Start a dependency-gated cluster session and record agent progress:

```powershell
$session = research-os cluster start $cluster
research-os cluster dispatch $session codex-coordinator
research-os cluster result $session codex-coordinator --status completed --summary "task graph ready"
```

Dispatch records are written as JSON envelopes. Claude Code dispatch can be executed explicitly:

```powershell
research-os cluster dispatch $session claude-literature-reviewer --execute
```

Distill a reusable skill draft:

```powershell
research-os distill skill $run
```

## Workspace Layout

Runtime outputs are written under `workspace/` and are ignored by git.

```text
workspace/
  intake/          structured research briefs
  evidence/        source ledgers
  bundles/         paper/task bundles
  cross_ideas/     cross-paper idea atoms and innovation candidates
  idea_reviews/    independent review records for innovation candidates
  repro_plans/     baseline-first reproduction plans
  cluster_plans/   Codex, Claude Code, runner, and verifier coordination plans
  cluster_sessions/ dependency-gated agent acknowledgement and result state
  cluster_dispatches/ provider-specific prompt and command envelopes
  runs/            baseline run records
  branches/        candidate branch sets
  rankings/        scored branch results
  redline_audits/  integrity reports
  memory/          distilled run metadata
  exports/         generated skill markdown
```

## Architecture

```text
src/research_os/
  cli.py              command surface
  ingest/             prompt parsing and domain hints
  web_research/       arXiv, GitHub, and Hugging Face evidence adapters
  bundle_builder/     brief + evidence -> paper bundle
  innovation/         cross-paper idea extraction and synthesis
  reproduce/          bundle -> baseline reproduction plan
  execution/          run records and checklist execution
  orchestration/      agent cluster planning, handoff prompts, and session state
  ideation/           branch generation and ranking
  supervisor/         redline integrity audits
  runner/             local, SSH, and Slurm runner registry
  domains/            multimodal, generative, and world-model profiles
  distill/            run or bundle -> reusable skill draft
  models/             Pydantic record schemas
```

The main design rule is separation between the control plane and execution plane:

- The control plane owns evidence, decisions, plans, audits, rankings, and memory.
- The execution plane owns how work is run on local machines, remote hosts, clusters, or future GPU services.

## Verification

Run the test suite from the repository root:

```powershell
$env:PYTHONPATH = ".\src"
python -m pytest -q
```

Expected result:

```text
all tests pass
```

Run a CLI smoke test:

```powershell
$env:PYTHONPATH = ".\src"
python -m research_os.cli intake "optimize a multimodal VQA baseline with code and datasets"
```

Expected result:

```text
workspace/intake/<brief-id>.json
```

## Project Principles

- Baseline first: no optimization branch should outrun reproduction.
- Evidence attached: claims should point back to source records.
- Cross-domain hypotheses: paper combinations are candidate hypotheses, not validated gains.
- Full-text provenance: when section text is available, ideas should point through section nodes before becoming candidates.
- Review before execution: cross-paper ideas should pass independent review before becoming branch candidates.
- Audit before ranking: gains are not useful if comparison integrity is broken.
- Local-first state: every major decision becomes a JSON artifact.
- Adapter-shaped execution: runners can change without rewriting the research workflow.
- Skill distillation: successful paths should become reusable operator knowledge.

## Roadmap

- Add richer source adapters for OpenReview, project pages, benchmark sites, and dataset portals.
- Add PDF-to-text ingestion and citation-span provenance for cross-paper synthesis.
- Add automatic patch planning for reviewed branch candidates after baseline recovery.
- Replace placeholder checklist execution with runner-specific baseline commands.
- Add real experiment branch execution across local, SSH, and Slurm backends.
- Add live Codex/Claude Code process launch and result collection behind the cluster session model.
- Store branch lineage across multiple optimization generations.
- Expand domain profiles for multimodal, generative, and world-model research.
- Integrate stronger provenance checks for metrics, datasets, and scripts.

## License

Research OS is released under the MIT License. See [LICENSE](LICENSE) for details.
