from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class RunRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    repro_plan_id: str
    runner: str
    status: str = "recorded"
    command: str = ""
    checklist: list[str]
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
