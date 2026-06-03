"""
Session Store — In-memory session state for multi-step workflows.

Stores task state across multiple request/response cycles.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionData:
    """State for a single user session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.goal: Optional[str] = None
        self.planned_steps: list[str] = []
        self.completed_steps: list[str] = []
        self.pending_steps: list[str] = []
        self.retry_count: int = 0
        self.last_page: Optional[str] = None
        self.last_error: Optional[str] = None
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def set_plan(self, goal: str, steps: list[str]):
        """Initialize a new task plan."""
        self.goal = goal
        self.planned_steps = list(steps)
        self.pending_steps = list(steps)
        self.completed_steps = []
        self.retry_count = 0
        self.updated_at = datetime.utcnow()

    def get_current_step(self) -> Optional[str]:
        """Get the next pending step."""
        return self.pending_steps[0] if self.pending_steps else None

    def complete_current_step(self):
        """Mark the current step as completed and move to next."""
        if self.pending_steps:
            step = self.pending_steps.pop(0)
            self.completed_steps.append(step)
            self.retry_count = 0
            self.updated_at = datetime.utcnow()

    def increment_retry(self):
        """Increment retry count for current step."""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def is_task_complete(self) -> bool:
        """Check if all steps are done."""
        return len(self.pending_steps) == 0 and len(self.completed_steps) > 0

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "goal": self.goal,
            "planned_steps": self.planned_steps,
            "completed_steps": self.completed_steps,
            "pending_steps": self.pending_steps,
            "retry_count": self.retry_count,
            "last_page": self.last_page,
        }

    @classmethod
    def from_dict(cls, session_id: str, data: dict) -> "SessionData":
        """Restore from API request task_state."""
        session = cls(session_id)
        if data:
            session.goal = data.get("goal")
            session.planned_steps = data.get("planned_steps", [])
            session.completed_steps = data.get("completed_steps", [])
            session.pending_steps = data.get("pending_steps", [])
            session.retry_count = data.get("retry_count", 0)
            session.last_page = data.get("last_page")
        return session


class SessionStore:
    """In-memory store for active sessions with TTL-based expiry."""

    def __init__(self, ttl_minutes: int = 30):
        self._sessions: dict[str, SessionData] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def get(self, session_id: str) -> SessionData:
        """Get or create a session."""
        self._cleanup()
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionData(session_id)
        return self._sessions[session_id]

    def get_or_restore(self, session_id: str, task_state: dict | None) -> SessionData:
        """Get existing session or restore from client-provided task_state."""
        self._cleanup()
        if session_id in self._sessions:
            return self._sessions[session_id]

        session = SessionData.from_dict(session_id, task_state or {})
        self._sessions[session_id] = session
        return session

    def remove(self, session_id: str):
        """Remove a completed session."""
        self._sessions.pop(session_id, None)

    def _cleanup(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.updated_at > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]


# Singleton instance
session_store = SessionStore()
