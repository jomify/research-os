from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class ResearchBrief(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    prompt: str
    objective: str
    domain_hints: list[str] = Field(default_factory=list)
    requires_code: bool = False
    requires_datasets: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_prompt(
        cls,
        prompt: str,
        domain_hint: str | None = None,
        domain_hints: list[str] | None = None,
    ) -> "ResearchBrief":
        lowered = prompt.lower()
        objective = "optimize" if any(token in lowered for token in ("optimiz", "improv")) or "\u4f18\u5316" in prompt else "reproduce"
        hints = list(domain_hints or [])
        if domain_hint and domain_hint not in hints:
            hints.append(domain_hint)
        code_tokens = ("code", "repo", "repository", "github")
        dataset_tokens = ("dataset", "datasets", "benchmark")
        return cls(
            prompt=prompt,
            objective=objective,
            domain_hints=hints,
            requires_code=(any(token in lowered for token in code_tokens) or "\u4ee3\u7801" in prompt),
            requires_datasets=(any(token in lowered for token in dataset_tokens) or "\u6570\u636e\u96c6" in prompt),
        )
