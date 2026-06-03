from pydantic import BaseModel, Field
from typing import Optional


class ActionDetail(BaseModel):
    type: str  # click | type | select | scroll | wait | navigate
    selector: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    direction: Optional[str] = None  # for scroll
    amount: Optional[int] = None  # for scroll
    duration_ms: Optional[int] = None  # for wait
    url: Optional[str] = None  # for navigate


class GuideStep(BaseModel):
    step: int
    instruction: str
    highlight_selector: Optional[str] = None


class TaskState(BaseModel):
    goal: Optional[str] = None
    planned_steps: list[str] = Field(default_factory=list)
    completed_steps: list[str] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)
    retry_count: int = 0
    last_page: Optional[str] = None


class OrchestratorResponse(BaseModel):
    session_id: str
    message: str
    mode: str  # action | guide | knowledge
    next_action: Optional[ActionDetail] = None
    actions: Optional[list[ActionDetail]] = None  # backward compat for guide
    guide_steps: Optional[list[GuideStep]] = None
    done: bool = False
    follow_up: Optional[str] = None
    task_state: Optional[TaskState] = None
