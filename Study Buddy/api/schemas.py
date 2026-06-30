from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Document Schemas ---

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    status: str # "processing" or "ready"

# --- Chat & Session Schemas ---

class ChatRequest(BaseModel):
    session_id: str
    message: str

class QuizQuestionModel(BaseModel):
    question: str
    options: Optional[List[str]] = None # For multiple choice
    answer: str
    explanation: Optional[str] = None

class QuizModel(BaseModel):
    topic: str
    questions: List[QuizQuestionModel]

class ChatResponse(BaseModel):
    response: str
    quiz_triggered: bool = False
    quiz_data: Optional[QuizModel] = None

# --- Quiz Schemas ---

class QuizResultRequest(BaseModel):
    topic: str
    correct: bool

class QuizResultResponse(BaseModel):
    topic: str
    accuracy: float
    message: str

# --- User Stats Schemas ---

class TopicRecordSchema(BaseModel):
    topic: str
    accuracy: float
    times_quizzed: int
    needs_review: bool

class UserStatsResponse(BaseModel):
    total_sessions: int
    topics: List[TopicRecordSchema]
