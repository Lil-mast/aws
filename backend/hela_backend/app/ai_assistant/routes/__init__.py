"""AI assistant endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_assistant.schemas import ChatRequest, ChatResponse
from app.ai_assistant.services.conversation_manager import handle_chat
from app.users.models import User
from core.database import get_db
from core.security import get_current_user

router = APIRouter(tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    content, conversation_id, model_used = await handle_chat(
        db=db,
        user_id=current_user.id,
        user_message=body.message,
        task_type=body.task_type,
        conversation_id=body.conversation_id,
    )
    return ChatResponse(
        conversation_id=conversation_id,
        message=content,
        model_used=model_used,
    )
