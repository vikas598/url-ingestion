from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel
from typing import Optional
from app.services.ai.chat_handler import handle_user_message
import uuid

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    response: Response,
    session_id: Optional[str] = Cookie(default=None)
):
    """
    Endpoint to interact with the AI shopping assistant.
    Session is managed automatically via cookies.
    """
    try:
        # 1️⃣ Create session if missing
        if session_id is None:
            session_id = str(uuid.uuid4())
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                max_age=30 * 60  # must match session timeout
            )

        # 2️⃣ Handle chat
        response_text = handle_user_message(
            session_id=session_id,
            user_input=request.message
        )

        return ChatResponse(response=response_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
