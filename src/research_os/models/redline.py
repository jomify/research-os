from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class RedlineCheck(BaseModel):
    area: str
    status: str
    message: str


class RedlineAudit(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    subject_type: str
    subject_id: str
    source_path: str
    checks: list[RedlineCheck]
    summary: dict[str, int]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
