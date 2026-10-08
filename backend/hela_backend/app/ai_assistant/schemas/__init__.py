"""Request and response schemas for Mula's AI assistant."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: UUID | None = None
    task_type: str = Field(default="chat", max_length=50)


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: str
    model_used: str
