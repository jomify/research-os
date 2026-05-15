from pathlib import Path
from typing import Any

from research_os.models.redline import RedlineAudit, RedlineCheck


CHECK_AREAS = ("metric", "dataset", "split", "script", "output", "constraint")


def build_redline_audit(source_path: Path, payload: dict[str, Any]) -> RedlineAudit:
    subject_type = _subject_type(payload)
    subject_id = str(payload.get("id") or source_path.stem)
    checks = [_check_area(area, payload) for area in CHECK_AREAS]
    summary = {
        "total": len(checks),
        "pass": sum(1 for check in checks if check.status == "pass"),
        "warn": sum(1 for check in checks if check.status == "warn"),
    }
    return RedlineAudit(
        subject_type=subject_type,
        subject_id=subject_id,
        source_path=str(source_path),
        checks=checks,
        summary=summary,
    )


def _subject_type(payload: dict[str, Any]) -> str:
    if "checklist" in payload and "bundle_id" in payload:
        return "repro_plan"
    if "brief_id" in payload and "evidence" in payload:
        return "bundle"
    return "json"


def _check_area(area: str, payload: dict[str, Any]) -> RedlineCheck:
    if _has_integrity_signal(area, payload):
        return RedlineCheck(
            area=area,
            status="pass",
            message=f"{area} integrity signal found",
        )
    return RedlineCheck(
        area=area,
        status="warn",
        message=f"{area} integrity signal missing or not explicit",
    )


def _has_integrity_signal(area: str, payload: dict[str, Any]) -> bool:
    keys = _flatten_keys(payload)
    text = _flatten_text(payload)
    if area in keys or f"{area}s" in keys:
        return True
    if area == "metric":
        return "metric" in text or "metrics" in text
    if area == "dataset":
        return "dataset" in text or "datasets" in text
    if area == "split":
        return "split" in text or "splits" in text
    if area == "script":
        return bool({"script", "scripts", "entrypoint", "entrypoints"} & keys) or "script" in text
    if area == "output":
        return bool({"output", "outputs", "result", "results"} & keys) or "output" in text
    if area == "constraint":
        return bool({"constraint", "constraints", "baseline_required"} & keys)
    return False


def _flatten_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set()
        for key, child in value.items():
            keys.add(str(key).lower())
            keys.update(_flatten_keys(child))
        return keys
    if isinstance(value, list):
        keys = set()
        for child in value:
            keys.update(_flatten_keys(child))
        return keys
    return set()


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_text(child) for child in value.values()).lower()
    if isinstance(value, list):
        return " ".join(_flatten_text(child) for child in value).lower()
    if isinstance(value, str):
        return value.lower()
    return ""
