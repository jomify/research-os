from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


SourceDomain = str
IdeaAtomFamily = Literal[
    "architecture",
    "algorithm",
    "theory",
    "data",
    "evaluation",
    "bio_neuro",
    "optimization",
]


class PaperSignal(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    evidence_id: str
    source_domain: SourceDomain
    source_url: str
    claim: str
    extracted_terms: list[str] = Field(default_factory=list)
    section_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class PaperSection(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    evidence_id: str
    section_name: str
    text: str
    extracted_terms: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class IdeaAtom(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    evidence_id: str
    section_id: str = ""
    source_domain: SourceDomain
    family: IdeaAtomFamily
    mechanism: str
    transfer_hint: str
    constraints: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class AgentContribution(BaseModel):
    agent_id: str
    role: str
    source_domains: list[SourceDomain]
    findings: list[str] = Field(default_factory=list)
    atom_ids: list[str] = Field(default_factory=list)


class InnovationCandidate(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    source_atom_ids: list[str]
    source_domains: list[SourceDomain]
    synthesis_agent: str
    hypothesis: str
    mechanism: str
    why_compatible: str
    expected_gain: str
    risk: str
    required_code_surface: list[str] = Field(default_factory=list)
    redline_notes: list[str] = Field(default_factory=list)
    score: float = 0.0


class IdeaGraphNode(BaseModel):
    id: str
    kind: str
    label: str
    source_domain: SourceDomain = "unknown"


class IdeaGraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str


class CrossPaperInnovationSet(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    bundle_id: str
    agent_contributions: list[AgentContribution]
    paper_signals: list[PaperSignal]
    paper_sections: list[PaperSection] = Field(default_factory=list)
    idea_atoms: list[IdeaAtom]
    innovation_candidates: list[InnovationCandidate]
    idea_graph_nodes: list[IdeaGraphNode] = Field(default_factory=list)
    idea_graph_edges: list[IdeaGraphEdge] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IdeaReviewFinding(BaseModel):
    candidate_id: str
    verdict: Literal["pass", "revise", "reject"]
    severity: Literal["info", "warning", "critical"]
    rationale: str
    required_action: str


class IdeaReviewRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    innovation_set_id: str
    proposer_provider: str
    reviewer_provider: str
    status: Literal["created", "completed", "failed"] = "created"
    prompt: str
    command: str
    command_args: list[str] = Field(default_factory=list)
    findings: list[IdeaReviewFinding] = Field(default_factory=list)
    summary: str = ""
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
