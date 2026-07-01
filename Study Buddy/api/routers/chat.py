from fastapi import APIRouter, Depends
from api.schemas import ChatRequest, ChatResponse
from agents.study_buddy import generate_agent_response

from api.dependencies import get_current_user

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Send a message to the agent and receive a response.
    """
    # Note: in a production setting, this could take several seconds. 
    # For a better UX, consider StreamingResponse or WebSockets later.
    response = generate_agent_response(
        user_id=user_id,
        session_id=request.session_id,
        user_message=request.message
    )
    return response
