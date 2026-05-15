# Research OS Design

Date: `2026-04-26`
Topic: `research-os`
Status: `draft-for-review`

## Objective

Build a new project under `E:\WORKSPACE\AI工具\research-os` that turns the AutoSOTA research pattern into a usable local-first research operating system for:

- paper reproduction
- baseline recovery
- automated optimization
- parallel branch search
- latest-paper-guided model modification
- multimodal, generative-model, and world-model specialization
- local and remote GPU or cluster execution
- reusable skill distillation from successful runs

The first version should integrate with existing tools where they already solve part of the problem well:

- `autoresearch` for compact experiment-loop kernels
- `OMX` for orchestration, state, memory, trace, wiki, and code-intel
- `MCP` for external systems and online knowledge surfaces

This project is not a generic agent shell. It is a research execution system focused on the path:

`natural-language goal -> evidence-backed candidate tasks -> reproduction -> audited optimization -> branch selection -> iteration -> skill distillation`

## Non-Goals

The first version does not aim to:

- be a fully general AutoML platform for arbitrary tabular or classical ML tasks
- replace Slurm, Ray, or Kubernetes schedulers
- auto-author papers or claims without evidence
- support every research area equally well
- guarantee true novelty beyond benchmark improvement
- directly manage large-scale distributed training internals

## Product Shape

The system has two planes:

- `control plane`
  - intake, web research, evidence ledger, paper bundling, reproduction planning, ideation, redline auditing, branch management, ranking, memory, and skill distillation
- `execution plane`
  - actual task execution on local or remote compute

The control plane is domain-aware and runner-agnostic.

The execution plane is runner-specific and domain-agnostic.

## Core User Story

A user can express a research goal in natural language, for example:

- "Find recent world-model papers with code and datasets, reproduce a feasible baseline on 24 GB VRAM, and search for improvements."
- "For a diffusion transformer image generation repo, automatically discover low-risk and structural optimization directions from recent related papers and evaluate them in parallel."
- "For multimodal medical VQA, gather benchmark-ready papers and datasets, recover a baseline, and optimize it under reproducibility constraints."

From that one request, the system should:

1. parse the request into a structured research brief
2. search the web for papers, code, datasets, and task constraints
3. build an evidence ledger with citations and timestamps
4. create one or more paper bundles
5. score feasibility against available compute and reproducibility signals
6. recover a baseline
7. construct a constrained idea library
8. generate multiple research branches in parallel
9. audit every branch against redline rules
10. execute valid experiments across available runners
11. rank results by metric, cost, stability, and complexity
12. keep the strongest branches as parents for the next generation
13. distill stable successes into reusable notes and skills

## Domain Scope

The first release specializes in three research families:

- `multimodal`
- `generative`
- `world_model`

Each family contributes:

- intake hints and query expansion templates
- benchmark and metric templates
- dataset and code availability heuristics
- domain-specific redline rules
- idea-generation priors
- failure signatures and replayable repair patterns

## System Modules

### 1. Ingest

Purpose:

- turn natural-language research goals into structured internal state

Inputs:

- one or more free-form user prompts
- optional paper URLs, repo URLs, dataset names, or local files

Outputs:

- `research brief`

Responsibilities:

- parse task type, modality, evaluation intent, compute limits, time range, code-availability requirements, dataset requirements, and optimization intent
- normalize the request into explicit fields
- tag likely domain family or families
- trigger web research using structured subqueries

### 2. Web Research

Purpose:

- retrieve source material and constraints from the web in a verifiable way

Primary sources:

- arXiv
- OpenReview
- conference pages
- project pages
- GitHub repositories
- Hugging Face repositories and datasets
- official benchmark sites
- official dataset pages

Outputs:

- `evidence ledger`
- candidate paper list
- candidate repo list
- candidate dataset list

Responsibilities:

- perform query expansion from the research brief
- keep evidence attached to each conclusion
- store URL, retrieval time, source type, extracted claim, and confidence
- avoid treating secondary summaries as ground truth when a primary source exists

### 3. Bundle Builder

Purpose:

- convert candidate tasks into standardized execution-ready units

Outputs:

- `paper bundle`

A paper bundle contains:

- canonical task name
- paper metadata
- code repository location
- dataset locations
- benchmark and metric definitions
- compute estimates
- baseline reproduction risk
- optimization opportunities
- redline-sensitive constraints

### 4. Reproduce

Purpose:

- recover an executable and comparable baseline before any optimization loop starts

Outputs:

- `repro plan`
- `baseline run record`

Responsibilities:

- environment inspection
- dependency recovery
- dataset presence checks
- baseline command discovery
- baseline metric capture
- comparability validation

The reproduction module may use:

- native project-specific adapters
- `autoresearch`-style kernels when the target can be expressed as iterative code-edit-and-eval loops

### 5. Ideation

Purpose:

- construct a constrained library of optimization ideas

Outputs:

- `idea library`

Idea categories:

- parameter tuning
- training strategy changes
- structure changes
- data and augmentation changes
- inference-time changes
- latest-paper-inspired transfer ideas

Each idea stores:

- hypothesis text
- source rationale
- parent paper or prior run
- estimated risk
- estimated cost
- expected effect
- required code surface
- redline notes

### 6. Supervisor

Purpose:

- enforce scientific validity and reject invalid shortcuts

Outputs:

- `redline audit report`

Hard rule families:

- `metric integrity`
- `dataset integrity`
- `split integrity`
- `script integrity`
- `output integrity`
- `constraint integrity`

Domain-specific examples:

- multimodal
  - hidden OCR, ASR, caption, or retrieval supervision not present in the baseline protocol
- generative
  - reporting gains from changed sampling budget, guidance, or post-processing without marking the comparison as non-equivalent
- world model
  - changing rollout horizon, seeds, conditioning, or simulator protocol while claiming baseline comparability

The supervisor runs twice:

- before execution
- after result collection

### 7. Runner

Purpose:

- execute experiments on different compute backends through a unified interface

First-version runners:

- `local`
- `ssh`
- `slurm`

Common runner responsibilities:

- job packaging
- environment setup invocation
- command launch
- timeout and retry policy
- log capture
- artifact collection
- status reporting

### 8. Memory

Purpose:

- preserve what the system learns across runs

Memory layers:

- per-run local memory
- cross-paper global memory
- normalized failure signatures
- successful repair patterns
- validated optimization patterns
- distilled skills

The memory module should prevent repeated blind retries of equivalent failed fixes.

### 9. Orchestrator

Purpose:

- manage the full lifecycle and state machine

Canonical flow:

`research brief`
-> `evidence ledger`
-> `paper bundle`
-> `repro plan`
-> `baseline run`
-> `idea library`
-> `parallel branch set`
-> `redline-cleared experiments`
-> `result ranking`
-> `survivor selection`
-> `next-generation branching`
-> `distilled notes and skills`

### 10. Distillation

Purpose:

- convert stable insights into durable operator assets

Outputs:

- optimization notes
- branch summaries
- reproducibility notes
- reusable skill drafts

## Parallel Branch Search

The optimization engine is a constrained research search tree, not a single-path tuner.

Every generation:

1. starts from one or more parent baselines or survivor branches
2. produces multiple branch families
3. expands each family into concrete experiment candidates
4. audits candidates
5. executes valid candidates in parallel
6. ranks them with multi-objective scoring
7. keeps one or more survivors for the next generation

Branch families include:

- pure hyperparameter search
- training-procedure search
- architecture search within bounded code surfaces
- data or augmentation search
- evaluation-aware but valid inference search
- latest-paper transfer branches

Branch records must preserve:

- parent branch
- source idea
- git or patch snapshot
- redline report
- run configuration
- metric outputs
- resource cost
- keep or reject status

## Ranking and Survivor Selection

Selection is not based on one metric alone.

First-version ranking signals:

- primary metric improvement
- secondary metric stability
- run success rate
- resource cost
- code complexity delta
- protocol comparability confidence
- future branchability

Possible outcomes:

- best absolute improvement survives
- moderate but stable and cheap branch survives over fragile expensive branch
- more than one branch survives if they represent distinct promising directions

## Integrations

### Autoresearch

Used as:

- a compact experiment kernel for targets that fit the edit-run-measure-keep-or-revert loop

Not used as:

- the entire orchestration system

### OMX

Used as:

- orchestration support
- state and memory support
- trace support
- wiki capture
- code intelligence support

### MCP

Used as:

- external knowledge and collaboration surface
- remote paper, dataset, repo, and workspace integration layer

Likely first-value connectors:

- Notion
- GitHub
- Hugging Face

## Data Model

The first version should have explicit schemas for:

- `ResearchBrief`
- `EvidenceItem`
- `EvidenceLedger`
- `PaperBundle`
- `ReproPlan`
- `BaselineRecord`
- `Idea`
- `IdeaLibrary`
- `RedlineAudit`
- `Branch`
- `ExperimentSpec`
- `RunRecord`
- `RankedResult`
- `DistilledSkillRecord`

These schemas are the contract between modules and should remain domain-agnostic with domain-specific extension fields.

## Project Layout

```text
research-os/
  README.md
  pyproject.toml
  docs/
    superpowers/
      specs/
  src/research_os/
    cli.py
    models/
    orchestrator/
    ingest/
    web_research/
    reproduce/
    ideation/
    supervisor/
    runner/
      local/
      ssh/
      slurm/
    memory/
    integrations/
      autoresearch/
      omx/
      mcp/
    domains/
      multimodal/
      generative/
      world_model/
  configs/
    runners/
    domains/
    redlines/
  templates/
    paper_bundle/
    repro_plan/
    experiment/
    distilled_skill/
  workspace/
    intake/
    bundles/
    runs/
    memory/
    evidence/
    exports/
  skills/
    autosota-research-loop/
      SKILL.md
```

## CLI Surface

The first CLI should expose these operations:

- `research-os intake "<natural language goal>"`
- `research-os bundle create --from-intake <id>`
- `research-os repro plan <bundle>`
- `research-os run baseline <bundle> --runner <runner>`
- `research-os ideate <bundle>`
- `research-os run branches <bundle> --runner <runner>`
- `research-os rank <bundle-or-generation>`
- `research-os distill skill <bundle-or-run>`

The CLI should feel orchestration-first, not library-first.

## Skill Surface

The first bundled skill should be:

- `autosota-research-loop`

Its purpose:

- tell a future agent when to use this project
- define the correct operator sequence
- ensure that natural-language intake, evidence collection, redline auditing, baseline recovery, branch execution, and skill distillation are invoked in the right order

This skill is not a marketing artifact. It is an operator protocol.

## Risks

Main risks:

- web research returns attractive but low-quality secondary sources
- reproduction cost balloons before baseline recovery
- idea generation drifts into invalid benchmark shortcuts
- branch explosion outruns available compute
- remote runner variability harms comparability
- agent memory captures noisy local fixes as if they were reusable truths

Mitigations:

- evidence ledger and primary-source preference
- feasibility filter before bundle creation
- mandatory baseline gate before ideation
- pre-run and post-run redline audits
- capped branch budgets per generation
- explicit runner metadata in every run record
- skill distillation only from repeated or independently validated wins

## Milestones

### Milestone 1

Deliver a runnable control-plane skeleton with:

- project structure
- CLI
- core schemas
- intake
- evidence ledger
- paper bundle generation
- local, ssh, and slurm runner interfaces
- first domain templates
- first skill

### Milestone 2

Deliver baseline recovery and audited branch execution with:

- reproduction planner
- baseline capture
- idea library
- redline engine
- parallel branch scheduling
- result ranking

### Milestone 3

Deliver persistent research memory and skill distillation with:

- failure signature normalization
- successful repair retrieval
- optimization note export
- distilled skill generation

## Final Decision

The new project should be implemented as a research operating system centered on:

- natural-language research intake
- evidence-backed task discovery
- reproducible baseline recovery
- AutoSOTA-style redline governance
- parallel branch search
- local and remote execution support
- durable memory and skill distillation

The first version should optimize for real execution over perfect conceptual mirroring of the AutoSOTA paper, while still preserving the paper's strongest ideas:

- closed-loop automation
- constrained ideation
- execution scheduling
- scientific validity checks
- memory-augmented repair
- iterative search over research directions
