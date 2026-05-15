---
name: autosota-research-loop
description: Use when operating research-os from a natural-language research goal through evidence-backed selection, redline-audited reproduction, parallel branch optimization, and skill distillation.
---

# AutoSOTA Research Loop

Use this skill when the task is to turn a research request into a controlled `research-os` execution loop instead of an ad hoc paper chase or one-off experiment.

## When To Use

- The user starts from a natural-language research objective.
- The task needs paper, code, dataset, and benchmark selection backed by recorded evidence.
- The work must recover a comparable baseline before optimization.
- The plan needs parallel branch exploration under explicit redline guardrails.

## Required Operator Sequence

1. Start with `research-os intake "<goal>"` to convert the free-form request into a structured brief.
2. Build the evidence ledger and use it for evidence-backed selection of papers, repos, datasets, and benchmark constraints.
3. Create the bundle from the intake record only after the sources, feasibility, and reproducibility signals are attached.
4. Recover the baseline before proposing branch modifications or claiming any optimization path is valid.
5. Run a redline audit on the reproduction plan and again on every optimization candidate.
6. Generate parallel branches from the cleared baseline, preserving parent branch, idea source, patch state, run configuration, and keep-or-reject status.
7. Rank branch outcomes by metric, stability, cost, and comparability confidence before selecting survivors.
8. Distill repeated wins and stable repair patterns into notes or follow-on skills only after the evidence is recorded.

## Guardrails

- Never skip `research-os intake`; the loop starts from structured intake, not from improvised commands.
- Never treat secondary summaries as enough when a primary paper, repo, dataset page, or benchmark source is available.
- Never optimize before a baseline exists and is reproducible on the selected runner.
- Never allow a branch to proceed without redline review of metric, dataset, split, script, and constraint integrity.
- Never report gains from non-comparable settings as if they were baseline-equivalent improvements.
- Never let parallel branches explode without a branch budget and survivor selection rule.

## Branch Discipline

- Parallel branches are search instruments, not excuses to run untracked experiments.
- Each branch should represent one bounded idea family or a clearly stated transfer hypothesis.
- Reject branches that are expensive, fragile, or redline-unsafe even if they show short-term metric movement.
