import tiktoken
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from database.firebase_client import db

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = "openai/gpt-4o-mini"

class ConversationMemory:
    """
    Sliding window with summarization.
    
    Keeps the last N messages verbatim. When the history grows beyond
    a token budget, the oldest messages are summarized into a single
    'memory block' that replaces them.
    """
    
    def __init__(self, session_id: str, max_tokens: int = 3000, keep_last_n: int = 6):
        self.session_id = session_id
        self.max_tokens = max_tokens
        self.keep_last_n = keep_last_n
        self.messages: list[dict] = []
        self.summary: str = ""   # compressed memory of older turns
        self._enc = tiktoken.get_encoding("cl100k_base")
        self.load()
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._maybe_compress()
        self.save()
    
    def _token_count(self) -> int:
        total = len(self._enc.encode(self.summary))
        for msg in self.messages:
            total += len(self._enc.encode(msg.get("content", "")))
        return total
    
    def _maybe_compress(self):
        """If we exceed the budget, summarize the oldest messages."""
        if self._token_count() <= self.max_tokens:
            return
        
        # Keep the most recent keep_last_n messages verbatim
        to_compress = self.messages[:-self.keep_last_n]
        self.messages = self.messages[-self.keep_last_n:]
        
        if not to_compress:
            return
        
        # Ask the model to compress
        compress_prompt = (
            "Summarize this conversation in 3–5 bullet points. "
            "Focus on: what topics were discussed, what the user understood well, "
            "what the user struggled with, and any facts or conclusions reached.\n\n"
        )
        compress_prompt += "\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in to_compress
        )
        
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": compress_prompt}]
        )
        new_summary = response.choices[0].message.content or ""
        
        # Prepend to existing summary
        if self.summary:
            self.summary = f"EARLIER CONTEXT:\n{self.summary}\n\nMORE RECENT:\n{new_summary}"
        else:
            self.summary = new_summary

    def save(self):
        """Save conversation state to Firestore."""
        if not db:
            print("Firestore not initialized. Cannot save conversation.")
            return
            
        doc_ref = db.collection('sessions').document(self.session_id)
        data = {
            "messages": self.messages,
            "summary": self.summary
        }
        doc_ref.set(data, merge=True)
    
    def load(self):
        """Load conversation state from Firestore."""
        if not db:
            print("Firestore not initialized. Cannot load conversation.")
            return
            
        doc_ref = db.collection('sessions').document(self.session_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict() or {}
            self.messages = data.get("messages", [])
            self.summary = data.get("summary", "")

    def get_messages_for_api(self, system_prompt: str) -> list[dict]:
        """Build the message list to send to the API."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if self.summary:
            messages.append({
                "role": "user",
                "content": f"[Memory of earlier conversation:\n{self.summary}]"
            })
            messages.append({
                "role": "assistant",
                "content": "Understood. I'll keep that context in mind."
            })
        
        messages.extend(self.messages)
        return messages