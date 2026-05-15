from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from research_os.models.memory import EvidenceReference


class DistilledSkillRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    source_id: str
    source_type: str
    name: str
    trigger: str
    guardrails: list[str]
    evidence_references: list[EvidenceReference]
    draft_path: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
