from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from research_os.models.idea import IdeaFamily


class RankedBranchItem(BaseModel):
    rank: int
    candidate_id: str
    family: IdeaFamily
    score: float
    metric_improvement: float
    resource_cost: float
    complexity: int


class BranchRanking(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    parent_bundle_id: str
    items: list[RankedBranchItem]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
