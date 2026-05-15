from pydantic import BaseModel


class EvidenceReference(BaseModel):
    source_type: str
    url: str
    claim: str
    evidence_id: str | None = None
