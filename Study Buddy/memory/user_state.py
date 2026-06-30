import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from database.firebase_client import db

@dataclass
class TopicRecord:
    topic: str
    times_quizzed: int = 0
    times_correct: int = 0
    last_seen: Optional[str] = None
    
    @property
    def accuracy(self) -> float:
        if self.times_quizzed == 0:
            return 0.0
        return self.times_correct / self.times_quizzed
    
    @property
    def needs_review(self) -> bool:
        return self.times_quizzed >= 2 and self.accuracy < 0.70

@dataclass
class UserState:
    user_id: str
    topics: dict[str, TopicRecord] = field(default_factory=dict)
    total_sessions: int = 0
    last_session: Optional[str] = None
    
    def record_quiz_result(self, topic: str, correct: bool):
        if topic not in self.topics:
            self.topics[topic] = TopicRecord(topic=topic)
        record = self.topics[topic]
        record.times_quizzed += 1
        if correct:
            record.times_correct += 1
        record.last_seen = datetime.now().isoformat()
    
    def get_weak_topics(self, min_quizzes: int = 2) -> List[TopicRecord]:
        return [
            t for t in self.topics.values()
            if t.needs_review and t.times_quizzed >= min_quizzes
        ]
    
    def get_summary_for_agent(self) -> str:
        if not self.topics:
            return "No quiz history yet — this is the user's first session."
        
        weak = self.get_weak_topics()
        strong = [t for t in self.topics.values() if t.accuracy >= 0.80]
        
        lines = [f"User has completed {self.total_sessions} sessions."]
        if weak:
            weak_names = ", ".join(t.topic for t in sorted(weak, key=lambda x: x.accuracy))
            lines.append(f"Weak topics (need review): {weak_names}")
        if strong:
            strong_names = ", ".join(t.topic for t in strong[:5])
            lines.append(f"Strong topics: {strong_names}")
        return "\n".join(lines)
    
    def save(self):
        """Save UserState to Firestore."""
        if not db:
            print("Firestore not initialized. Cannot save state.")
            return
            
        doc_ref = db.collection('users').document(self.user_id)
        data = {
            "total_sessions": self.total_sessions,
            "last_session": self.last_session,
            "topics": {k: asdict(v) for k, v in self.topics.items()}
        }
        doc_ref.set(data, merge=True)
    
    @classmethod
    def load(cls, user_id: str) -> "UserState":
        """Load UserState from Firestore."""
        state = cls(user_id=user_id)
        if not db:
            print("Firestore not initialized. Returning empty state.")
            return state
            
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict() or {}
            state.total_sessions = data.get("total_sessions", 0)
            state.last_session = data.get("last_session")
            for topic_name, record_data in data.get("topics", {}).items():
                state.topics[topic_name] = TopicRecord(**record_data)
                
        return state