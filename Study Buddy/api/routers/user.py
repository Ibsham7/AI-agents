from fastapi import APIRouter, Depends
from api.schemas import UserStatsResponse, TopicRecordSchema
from memory.user_state import UserState

from api.dependencies import get_current_user

router = APIRouter()

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: str = Depends(get_current_user)):
    """
    Get user progress, accuracy, and weak topics.
    """
    user_state = UserState.load(user_id)
    
    topics = []
    for topic_name, record in user_state.topics.items():
        topics.append(TopicRecordSchema(
            topic=topic_name,
            accuracy=record.accuracy,
            times_quizzed=record.times_quizzed,
            needs_review=record.needs_review
        ))
        
    return UserStatsResponse(
        total_sessions=user_state.total_sessions,
        topics=topics
    )
