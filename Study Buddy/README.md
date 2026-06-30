# Study Buddy Backend API

This repository contains the backend for the **Study Buddy** application. It is built with **FastAPI**, uses **Pinecone** for vector search, and integrates with **Firebase** for authentication, database (Firestore), and file storage.

## 🏗 Architecture Overview

- **FastAPI**: Serves as the high-performance asynchronous web framework for our REST APIs.
- **Firebase Admin SDK**:
  - **Auth**: Validates user tokens.
  - **Cloud Storage**: Stores the raw uploaded PDFs.
  - **Firestore**: Stores user state (weak topics, session data, total sessions) and document tracking metadata.
- **Pinecone**: Serves as the Vector Database replacing the local ChromaDB. We extract text from PDFs, chunk it, run it through `SentenceTransformers` (`all-MiniLM-L6-v2`), and store the vectors in Pinecone for lightning-fast semantic search.
- **OpenRouter (LLM)**: Integrates with external LLMs to power the core agentic loop.

---

## 📁 Directory Structure

```text
.
├── main.py                     # Entry point for the FastAPI application
├── requirements.txt            # Python dependencies
├── instructions.md             # Setup guide for Firebase and Pinecone
├── .env.example                # Template for environment variables
├── api/
│   ├── schemas.py              # Pydantic models for strict API request/response validation
│   └── routers/
│       ├── docs.py             # Routes for PDF upload and listing
│       ├── chat.py             # Routes for interacting with the AI
│       ├── quiz.py             # Routes for updating quiz progress
│       └── user.py             # Routes for retrieving user study stats
├── database/
│   ├── firebase_client.py      # Initializes Firebase Admin SDK (Auth, Firestore, Storage)
│   └── pinecone_client.py      # Initializes Pinecone connection
├── agents/
│   └── study_buddy.py          # Core AI agent logic (LLM Orchestration & tool calling)
├── ingestion/
│   ├── embedder.py             # PDF ingestion, chunking, and upserting into Pinecone
│   ├── chunker.py              # Logic to slice text into semantic chunks
│   └── loader.py               # Logic to extract raw text from PDF files
├── retrieval/
│   └── retriever.py            # Queries Pinecone to find the most relevant document chunks
└── memory/
    ├── user_state.py           # Loads/Saves user study history and weak topics via Firestore
    └── conversation.py         # Manages sliding-window conversation memory via Firestore
```

---

## 🔌 API Endpoints Reference

### 1. Documents (`/docs`)

**`POST /docs/upload`**
- **Description**: Upload a course PDF to the system.
- **Behavior**: Saves the PDF to Firebase Cloud Storage, creates a tracking document in Firestore, and kicks off a background task that chunks the text, creates embeddings, and upserts them to Pinecone.
- **Payload**: `multipart/form-data` containing the `file`.
- **Returns**: `{"document_id": "<uuid>", "status": "processing"}`

**`GET /docs/`**
- **Description**: List all PDFs uploaded by the authenticated user.
- **Returns**: An array of objects containing the document `id`, `filename`, `upload_date`, and `status`.

### 2. Chat (`/chat`)

**`POST /chat/message`**
- **Description**: Send a message to the AI Study Buddy.
- **Payload Schema**:
  ```json
  {
    "session_id": "string",
    "message": "string"
  }
  ```
- **Behavior**: Loads conversation history from Firestore. Evaluates the user's question, uses tools (`search_notes`, `generate_quiz`) dynamically by retrieving context from Pinecone, and generates a response.
- **Returns Schema**:
  ```json
  {
    "response": "string (Agent's text response)",
    "quiz_triggered": boolean,
    "quiz_data": null | {
      "topic": "string",
      "questions": [
        {
          "question": "string",
          "options": ["string"],
          "answer": "string",
          "explanation": "string"
        }
      ]
    }
  }
  ```

### 3. Quiz (`/quiz`)

**`POST /quiz/result`**
- **Description**: Submits the result of a single quiz question to update the user's accuracy tracker.
- **Payload Schema**:
  ```json
  {
    "topic": "string",
    "correct": boolean
  }
  ```
- **Returns Schema**:
  ```json
  {
    "topic": "string",
    "accuracy": float,
    "message": "Quiz result saved successfully."
  }
  ```

### 4. User (`/user`)

**`GET /user/stats`**
- **Description**: Retrieve the user's study metrics, including strong topics, weak topics needing review, and the number of times they've been quizzed.
- **Returns Schema**:
  ```json
  {
    "total_sessions": integer,
    "topics": [
      {
        "topic": "string",
        "accuracy": float,
        "times_quizzed": integer,
        "needs_review": boolean
      }
    ]
  }
  ```

---

## 🚀 Running the Server Locally

1. Follow the setup steps in `instructions.md` to configure Pinecone and Firebase.
2. Rename `.env.example` to `.env` and fill in your keys.
3. Place your `firebase-adminsdk.json` in the root of the project.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # OR if requirements.txt is missing:
   # pip install fastapi uvicorn pinecone-client firebase-admin pydantic python-dotenv python-multipart sentence-transformers
   ```
5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
6. Access the interactive API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)
