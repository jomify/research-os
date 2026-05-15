from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    source_type: str
    url: str
    claim: str
    confidence: float = 0.5
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvidenceLedger(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)
