from pathlib import Path


def test_autosota_skill_mentions_parallel_branches_redline_and_intake() -> None:
    content = Path("skills/autosota-research-loop/SKILL.md").read_text(encoding="utf-8")
    lowered = content.lower()

    assert "parallel branch" in lowered
    assert "redline" in lowered
    assert "research-os intake" in lowered
    assert "baseline" in lowered
    assert "required operator sequence" in lowered
