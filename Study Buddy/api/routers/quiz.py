from fastapi import APIRouter
from api.schemas import QuizResultRequest, QuizResultResponse
from memory.user_state import UserState

router = APIRouter()

@router.post("/result", response_model=QuizResultResponse)
async def submit_quiz_result(
    request: QuizResultRequest,
    user_id: str = "default_user"
):
    """
    Record if a user got a specific quiz topic question right or wrong.
    """
    user_state = UserState.load(user_id)
    user_state.record_quiz_result(topic=request.topic, correct=request.correct)
    user_state.save()
    
    accuracy = user_state.topics[request.topic].accuracy
    
    return QuizResultResponse(
        topic=request.topic,
        accuracy=accuracy,
        message="Quiz result saved successfully."
    )
