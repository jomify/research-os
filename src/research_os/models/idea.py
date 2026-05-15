from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


IdeaFamily = Literal[
    "hyperparameter",
    "training_strategy",
    "architecture",
    "data",
    "inference",
    "paper_transfer",
]

IDEA_FAMILIES: tuple[IdeaFamily, ...] = (
    "hyperparameter",
    "training_strategy",
    "architecture",
    "data",
    "inference",
    "paper_transfer",
)


class Idea(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    family: IdeaFamily
    title: str
    rationale: str
    proposed_change: str
    expected_metric_direction: str = "increase"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
