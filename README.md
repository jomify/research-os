# Research OS

Research OS is a local-first research operating system for turning a natural-language research goal into evidence-backed tasks, reproducible baselines, audited experiment branches, and reusable research skills.

It is built for AutoSOTA-style workflows where the important question is not only "what should we try?", but also "can we reproduce the baseline, keep the comparison fair, and preserve the winning path for the next run?"

```text
goal
  -> intake
  -> evidence ledger
  -> paper bundle
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
  repro_plans/     baseline-first reproduction plans
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
  reproduce/          bundle -> baseline reproduction plan
  execution/          run records and checklist execution
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
- Audit before ranking: gains are not useful if comparison integrity is broken.
- Local-first state: every major decision becomes a JSON artifact.
- Adapter-shaped execution: runners can change without rewriting the research workflow.
- Skill distillation: successful paths should become reusable operator knowledge.

## Roadmap

- Add richer source adapters for OpenReview, project pages, benchmark sites, and dataset portals.
- Replace placeholder checklist execution with runner-specific baseline commands.
- Add real experiment branch execution across local, SSH, and Slurm backends.
- Store branch lineage across multiple optimization generations.
- Expand domain profiles for multimodal, generative, and world-model research.
- Integrate stronger provenance checks for metrics, datasets, and scripts.

## License

Research OS is released under the MIT License. See [LICENSE](LICENSE) for details.
