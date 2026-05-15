import json
import re
from pathlib import Path

from research_os.models.distill import DistilledSkillRecord
from research_os.models.memory import EvidenceReference


DEFAULT_GUARDRAILS = [
    "Never skip baseline recovery",
    "Prefer primary-source evidence before recommending an implementation path",
    "Do not claim gains without recorded metrics and source references",
]


def distill_skill(source_path: Path, workspace_dir: Path) -> tuple[DistilledSkillRecord, Path]:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    source_id = str(payload.get("id") or source_path.stem)
    source_type = _infer_source_type(payload)
    trigger = _infer_trigger(payload)
    evidence_references = _extract_evidence_references(payload, source_path)
    name = _skill_name(trigger)

    exports_dir = workspace_dir / "exports"
    memory_dir = workspace_dir / "memory"
    exports_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)

    draft_path = exports_dir / f"{name}.md"
    record = DistilledSkillRecord(
        source_id=source_id,
        source_type=source_type,
        name=name,
        trigger=trigger,
        guardrails=DEFAULT_GUARDRAILS,
        evidence_references=evidence_references,
        draft_path=str(draft_path),
    )
    draft_path.write_text(_render_skill_draft(record), encoding="utf-8")

    record_path = memory_dir / f"{record.id}.json"
    record_path.write_text(json.dumps(record.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    return record, record_path


def _infer_source_type(payload: dict) -> str:
    if "brief_id" in payload and "evidence" in payload:
        return "bundle"
    if "bundle_id" in payload:
        return "run"
    return str(payload.get("source_type") or "run")


def _infer_trigger(payload: dict) -> str:
    for key in ("title", "trigger", "prompt", "summary"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    command = payload.get("command")
    checklist = payload.get("checklist")
    if isinstance(command, str) and command.strip():
        checklist_text = ""
        if isinstance(checklist, list) and checklist:
            checklist_text = f" after: {', '.join(str(item) for item in checklist)}"
        return f"Use when rerunning `{command.strip()}`{checklist_text}."
    return "Use when repeating the distilled research workflow."


def _extract_evidence_references(payload: dict, source_path: Path) -> list[EvidenceReference]:
    raw_items = payload.get("evidence", {}).get("items", [])
    references = [
        EvidenceReference(
            evidence_id=item.get("id"),
            source_type=str(item.get("source_type") or "unknown"),
            url=str(item.get("url") or ""),
            claim=str(item.get("claim") or ""),
        )
        for item in raw_items
        if isinstance(item, dict)
    ]
    if references:
        return references
    return [
        EvidenceReference(
            source_type="source_json",
            url=str(source_path),
            claim="Input source record used for this distilled skill draft.",
        )
    ]


def _skill_name(trigger: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", trigger.lower()).strip("-")
    return (slug or "distilled-research-skill")[:64]


def _render_skill_draft(record: DistilledSkillRecord) -> str:
    template = _template_path().read_text(encoding="utf-8")
    guardrails = "\n".join(f"- {item}" for item in record.guardrails)
    evidence = "\n".join(
        f"- `{item.source_type}` {item.url}: {item.claim}" for item in record.evidence_references
    )
    return template.format(
        name=record.name,
        source_id=record.source_id,
        source_type=record.source_type,
        trigger=record.trigger,
        guardrails=guardrails,
        evidence_references=evidence,
    )


def _template_path() -> Path:
    return Path(__file__).resolve().parents[3] / "templates" / "distilled_skill" / "SKILL.md.tpl"
