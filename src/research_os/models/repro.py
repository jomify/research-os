from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from research_os.models.bundle import PaperBundle


class ReproPlan(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    bundle_id: str
    runner: str
    status: str = "planned"
    baseline_required: bool = True
    checklist: list[str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_bundle(cls, bundle: PaperBundle, runner: str) -> "ReproPlan":
        checklist = [
            "verify code repository availability",
            "verify dataset availability and split rules",
            "recover comparable baseline",
            "record metric command and baseline output",
        ]
        return cls(bundle_id=bundle.id, runner=runner, checklist=checklist)
