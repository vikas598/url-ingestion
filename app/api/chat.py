from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
from app.services.ai.chat_handler import handle_user_message

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    product_type: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    products: list = []


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    response: Response,
):
    """
    Endpoint to interact with the AI shopping assistant.
    Uses a single shared conversation history for all messages.
    """
    try:
        # Use a fixed session_id so all messages share one conversation
        session_id = "default"

        # Store product_type preference if provided
        if request.product_type is not None:
            from app.services.ai.conversation_store import update_memory
            update_memory(session_id, {"product_type": request.product_type})

        # 4️⃣ Handle chat
        response_text, products = handle_user_message(
            session_id=session_id,
            user_input=request.message
        )

        return ChatResponse(
            response=response_text, 
            products=products,
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
