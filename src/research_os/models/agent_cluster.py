from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


AgentProvider = Literal["codex", "claude_code", "runner", "verifier", "human"]
AgentStateStatus = Literal["ready", "blocked", "acknowledged", "completed", "failed"]
ClusterSessionStatus = Literal["active", "completed", "failed"]
DispatchStatus = Literal["created", "completed", "failed"]


class AgentAssignment(BaseModel):
    id: str
    provider: AgentProvider
    role: str
    responsibility: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)


class AgentHandoff(BaseModel):
    target_provider: AgentProvider
    title: str
    prompt: str
    command: str = ""


class AgentClusterPlan(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    source_id: str
    source_type: str
    objective: str
    coordinator: AgentProvider = "codex"
    agents: list[AgentAssignment]
    handoffs: list[AgentHandoff]
    execution_order: list[str]
    redline_gates: list[str]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentSessionState(BaseModel):
    agent_id: str
    provider: AgentProvider
    status: AgentStateStatus
    depends_on: list[str] = Field(default_factory=list)
    external_ref: str = ""
    notes: list[str] = Field(default_factory=list)
    result_summary: str = ""
    artifacts: list[str] = Field(default_factory=list)
    acknowledged_at: str = ""
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentClusterSession(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    plan_id: str
    source_id: str
    status: ClusterSessionStatus = "active"
    agent_states: list[AgentSessionState]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentDispatchRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    plan_id: str
    agent_id: str
    provider: AgentProvider
    status: DispatchStatus = "created"
    title: str
    prompt: str
    command: str
    command_args: list[str] = Field(default_factory=list)
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
