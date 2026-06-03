from pydantic import BaseModel, Field
from typing import Optional


class InteractiveElement(BaseModel):
    id: str
    tag: str
    text: Optional[str] = None
    selector: str
    aria_label: Optional[str] = None
    visible: bool = True


class DOMContext(BaseModel):
    url: str
    page_title: str
    interactive_elements: list[InteractiveElement] = Field(default_factory=list)
    visible_text_summary: Optional[str] = None


class TaskState(BaseModel):
    goal: Optional[str] = None
    planned_steps: list[str] = Field(default_factory=list)
    completed_steps: list[str] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)
    retry_count: int = 0
    last_page: Optional[str] = None


class OrchestratorRequest(BaseModel):
    session_id: str
    user_input: str
    mode: str = "action"  # action | guide
    context: DOMContext
    previous_actions: list[dict] = Field(default_factory=list)
    error_from_last_action: Optional[str] = None
    task_state: Optional[TaskState] = None
