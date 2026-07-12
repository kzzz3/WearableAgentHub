"""Message models for the agent system."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    AGENT = "agent"


class Message(BaseModel):
    """A single message in a conversation."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    """Incoming chat request from frontend."""

    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    """Response to a chat request."""

    reply: str
    a2ui_messages: list[dict] = Field(default_factory=list)
    session_id: str = "default"