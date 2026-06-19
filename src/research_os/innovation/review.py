from datetime import datetime, timezone
import subprocess

from research_os.models.innovation import (
    CrossPaperInnovationSet,
    IdeaReviewFinding,
    IdeaReviewRecord,
    InnovationCandidate,
)
from research_os.models.branch import BranchCandidate, BranchSet


def build_idea_review_record(
    innovation_set: CrossPaperInnovationSet,
    proposer_provider: str = "codex",
    reviewer_provider: str = "claude_code",
) -> IdeaReviewRecord:
    findings = [_heuristic_finding(candidate) for candidate in innovation_set.innovation_candidates]
    prompt = _review_prompt(innovation_set, proposer_provider, reviewer_provider)
    command, command_args = _review_command(reviewer_provider, prompt)
    return IdeaReviewRecord(
        innovation_set_id=innovation_set.id,
        proposer_provider=proposer_provider,
        reviewer_provider=reviewer_provider,
        prompt=prompt,
        command=command,
        command_args=command_args,
        findings=findings,
        summary=_summary(findings),
    )


def complete_idea_review(
    record: IdeaReviewRecord,
    status: str,
    returncode: int | None,
    stdout: str,
    stderr: str,
) -> IdeaReviewRecord:
    if status not in {"completed", "failed"}:
        raise ValueError("Idea review status must be 'completed' or 'failed'.")
    record.status = status
    record.returncode = returncode
    record.stdout = stdout
    record.stderr = stderr
    if stdout:
        record.summary = stdout[:500]
    elif stderr:
        record.summary = stderr[:500]
    record.updated_at = datetime.now(timezone.utc).isoformat()
    return record


def execute_claude_idea_review(record: IdeaReviewRecord, timeout: float = 300) -> dict[str, str | int]:
    if record.reviewer_provider != "claude_code":
        raise ValueError("Only claude_code idea reviews can be executed by this helper.")
    try:
        result = subprocess.run(
            record.command_args,
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


def build_branch_set_from_review(
    innovation_set: CrossPaperInnovationSet,
    review: IdeaReviewRecord,
    include_revise: bool = False,
) -> BranchSet:
    if review.innovation_set_id != innovation_set.id:
        raise ValueError("Idea review does not match the supplied cross-ideas record.")
    allowed_verdicts = {"pass", "revise"} if include_revise else {"pass"}
    findings = {
        finding.candidate_id: finding
        for finding in review.findings
        if finding.verdict in allowed_verdicts
    }
    candidates = [
        _branch_candidate_from_idea(innovation_set.bundle_id, candidate, findings[candidate.id])
        for candidate in innovation_set.innovation_candidates
        if candidate.id in findings
    ]
    if not candidates:
        raise ValueError("No reviewed idea candidates are eligible for branch conversion.")
    return BranchSet(parent_bundle_id=innovation_set.bundle_id, candidates=candidates)


def _heuristic_finding(candidate: InnovationCandidate) -> IdeaReviewFinding:
    if not candidate.redline_notes:
        return IdeaReviewFinding(
            candidate_id=candidate.id,
            verdict="reject",
            severity="critical",
            rationale="Candidate has no redline notes, so comparability constraints are not explicit.",
            required_action="Attach metric, dataset, split, protocol, and evidence constraints before execution.",
        )
    if len(candidate.source_domains) < 2:
        return IdeaReviewFinding(
            candidate_id=candidate.id,
            verdict="revise",
            severity="warning",
            rationale="Candidate is not cross-domain, so it does not satisfy the cross-paper synthesis goal.",
            required_action="Add another source atom from a distinct domain or downgrade to ordinary branch ideation.",
        )
    if candidate.score < 0.75:
        return IdeaReviewFinding(
            candidate_id=candidate.id,
            verdict="revise",
            severity="warning",
            rationale="Candidate score is low for immediate branch execution.",
            required_action="Strengthen provenance, compatibility rationale, or expected gain before execution.",
        )
    return IdeaReviewFinding(
        candidate_id=candidate.id,
        verdict="pass",
        severity="info",
        rationale="Candidate has cross-domain sources and explicit redline constraints.",
        required_action="Keep baseline-first reproduction and run redline audit before implementation.",
    )


def _branch_candidate_from_idea(
    bundle_id: str,
    candidate: InnovationCandidate,
    finding: IdeaReviewFinding,
) -> BranchCandidate:
    complexity = min(9, max(2, len(candidate.required_code_surface) + len(candidate.source_domains)))
    cost = round(1.0 + complexity * 0.75 + max(candidate.score, 0.0), 2)
    rationale = (
        f"Reviewed verdict: {finding.verdict}. {finding.rationale} "
        f"Sources: {', '.join(candidate.source_domains)}. Redlines: {'; '.join(candidate.redline_notes)}."
    )
    proposed_change = (
        f"Hypothesis: {candidate.hypothesis}\n"
        f"Mechanism: {candidate.mechanism}\n"
        f"Required action before execution: {finding.required_action}\n"
        f"Required code surface: {', '.join(candidate.required_code_surface) or 'unspecified'}"
    )
    return BranchCandidate(
        parent_bundle_id=bundle_id,
        family="paper_transfer",
        title=candidate.title,
        rationale=rationale,
        proposed_change=proposed_change,
        resource_cost_estimate=cost,
        complexity=complexity,
    )


def _summary(findings: list[IdeaReviewFinding]) -> str:
    counts = {
        "pass": sum(1 for finding in findings if finding.verdict == "pass"),
        "revise": sum(1 for finding in findings if finding.verdict == "revise"),
        "reject": sum(1 for finding in findings if finding.verdict == "reject"),
    }
    return f"pass={counts['pass']} revise={counts['revise']} reject={counts['reject']}"


def _review_prompt(
    innovation_set: CrossPaperInnovationSet,
    proposer_provider: str,
    reviewer_provider: str,
) -> str:
    candidate_lines = "\n".join(
        (
            f"- id={candidate.id}; title={candidate.title}; domains={','.join(candidate.source_domains)}; "
            f"score={candidate.score}; hypothesis={candidate.hypothesis}; redlines={'; '.join(candidate.redline_notes)}"
        )
        for candidate in innovation_set.innovation_candidates
    )
    return (
        "Review these Research OS cross-paper innovation candidates as an independent model.\n"
        f"Proposer provider: {proposer_provider}\n"
        f"Reviewer provider: {reviewer_provider}\n"
        f"Innovation set id: {innovation_set.id}\n"
        "Judge novelty plausibility, scientific comparability, benchmark safety, provenance, and execution risk.\n"
        "Do not request secrets, tokens, private credentials, or destructive permissions.\n"
        "Return concise findings with verdict pass/revise/reject and required action for each candidate.\n\n"
        f"Candidates:\n{candidate_lines}"
    )


def _review_command(reviewer_provider: str, prompt: str) -> tuple[str, list[str]]:
    if reviewer_provider == "claude_code":
        return "claude -p <idea-review-json.prompt> --permission-mode plan", [
            "claude",
            "-p",
            prompt,
            "--permission-mode",
            "plan",
        ]
    return "manual idea review", []
