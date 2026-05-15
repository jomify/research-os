from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from research_os.models.brief import ResearchBrief
from research_os.models.evidence import EvidenceLedger


class PaperBundle(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    brief_id: str
    title: str
    summary: str
    domain_hints: list[str] = Field(default_factory=list)
    evidence: EvidenceLedger = Field(default_factory=EvidenceLedger)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_brief(cls, brief: ResearchBrief, evidence: EvidenceLedger | None = None) -> "PaperBundle":
        title = brief.prompt[:80]
        summary = (
            f"{brief.objective.title()} workflow candidate"
            f" with domains: {', '.join(brief.domain_hints) or 'unspecified'}"
        )
        return cls(
            brief_id=brief.id,
            title=title,
            summary=summary,
            domain_hints=brief.domain_hints,
            evidence=evidence or EvidenceLedger(),
        )
