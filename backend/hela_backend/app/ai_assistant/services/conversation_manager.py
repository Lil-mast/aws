"""
app/ai_assistant/services/conversation_manager.py
──────────────────────────────────────────────────
Orchestrates multi-turn conversations:
  - Resolves or creates a Conversation record
  - Persists user and assistant messages
  - Passes conversation history to the Bedrock client
  - Updates the conversation title from the first user message
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant.models import Conversation, Message
from app.ai_assistant.services.bedrock_client import BedrockResponse, get_bedrock_client

logger = logging.getLogger(__name__)


async def handle_chat(
    db: AsyncSession,
    user_id: UUID,
    user_message: str,
    task_type: str = "chat",
    conversation_id: Optional[UUID] = None,
) -> tuple[str, UUID, str]:
    """
    Process a user message and return the assistant reply.

    Returns:
        (assistant_content, conversation_id, model_used)
    """
    client = get_bedrock_client()

    # ── Resolve conversation ──────────────────────────────────────────────────
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            conversation = None  # will create a new one

    if not conversation_id or conversation is None:
        conversation = Conversation(user_id=user_id, task_type=task_type)
        db.add(conversation)
        await db.flush()

    # Update task type if changed
    if conversation.task_type != task_type:
        conversation.task_type = task_type

    # ── Load history (last 20 messages for context) ───────────────────────────
    history_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(20)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_result.scalars().all()
        if m.role in ("user", "assistant")
    ]

    # ── Persist user message ──────────────────────────────────────────────────
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # ── Call AI ───────────────────────────────────────────────────────────────
    response: BedrockResponse = client.chat(
        task_type=task_type,
        user_message=user_message,
        conversation_history=history,
    )

    # ── Persist assistant message ─────────────────────────────────────────────
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response.content,
        model_used=response.model_used,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )
    db.add(assistant_msg)

    # ── Set conversation title from first user message ────────────────────────
    if conversation.title == "New conversation":
        conversation.title = user_message[:80]

    await db.flush()
    return response.content, conversation.id, response.model_used
