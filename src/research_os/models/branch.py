from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from research_os.models.idea import IdeaFamily


class BranchCandidate(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    parent_bundle_id: str
    family: IdeaFamily
    title: str
    rationale: str
    proposed_change: str
    resource_cost_estimate: float = 1.0
    complexity: int = 1


class BranchResult(BaseModel):
    candidate_id: str
    family: IdeaFamily
    metric_improvement: float
    resource_cost: float
    complexity: int


class BranchSet(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    parent_bundle_id: str
    candidates: list[BranchCandidate] = Field(default_factory=list)
    results: list[BranchResult] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
