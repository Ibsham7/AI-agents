# Week 3 — Memory & RAG
### Detailed Daily Workflow | Intensive Track (20+ hrs/week)

---

## What You Will Have Built by End of Week 3

A **Personalized Study Buddy** agent that:
- Ingests your own PDF course notes and textbooks into a local vector database
- Answers questions about the material using only what it retrieved — not hallucinated knowledge
- Generates quizzes on any topic from your notes
- Tracks which topics you get wrong across sessions and adapts future quizzes accordingly
- Explains *why* a retrieved chunk was relevant to a query

Every component — the ingestion pipeline, chunking, embedding, retrieval, memory — built and understood by you, not hidden inside a library.

---

## The Mental Model for This Week

In Weeks 1–2, every agent started fresh each run. No memory of previous conversations, no stored knowledge beyond what the model was trained on. That works fine for one-shot tasks (review this file, answer this query) but breaks the moment you need:

- The agent to know things from *your* documents (not its training data)
- The agent to remember what happened in *previous sessions*
- The agent to adapt its behavior based on *accumulated history*

RAG and memory are two different solutions to two different versions of this problem:

**RAG** (Retrieval-Augmented Generation) — solves the *knowledge* problem. The model doesn't know your course notes. You store them in a vector database, retrieve the relevant chunks at query time, and inject them into the context window. The model now "knows" your material — without fine-tuning.

**Memory** — solves the *continuity* problem. The model has no memory between sessions. You solve this by explicitly storing and retrieving past conversation summaries, quiz results, and user-specific state.

Both use the same underlying mechanic: embed → store → retrieve → inject into context.

---

## Before Day 1 — Setup (1–2 hrs)

### New packages for this week
```bash
pip install chromadb sentence-transformers pypdf rich tiktoken
```

| Package | What it does | Cost |
|---|---|---|
| `chromadb` | Local vector database, persists to disk | Free, local |
| `sentence-transformers` | Embeds text into vectors using local models | Free, local (downloads ~90MB model once) |
| `pypdf` | Extracts text from PDF files | Free |
| `tiktoken` | Counts tokens accurately (OpenAI's tokenizer) | Free |
| `rich` | Pretty terminal output for the REPL | Free |

> **On sentence-transformers:** the first run will download the embedding model (`all-MiniLM-L6-v2`, ~90MB) to your machine. After that it's fully offline. No API key, no usage limit, no cost. This is important — your embedding pipeline will work without any internet connection once the model is downloaded.

### Folder structure for Week 3
```
week3-agent/
├── .env
├── ingestion/
│   ├── __init__.py
│   ├── loader.py          # PDF → raw text
│   ├── chunker.py         # raw text → chunks
│   └── embedder.py        # chunks → vectors in ChromaDB
├── retrieval/
│   ├── __init__.py
│   └── retriever.py       # query → relevant chunks
├── memory/
│   ├── __init__.py
│   ├── conversation.py    # short-term: sliding window + summarization
│   └── user_state.py      # long-term: quiz scores, weak topics, session count
├── agents/
│   ├── __init__.py
│   └── study_buddy.py     # the full agent
├── tools/
│   ├── __init__.py
│   └── schemas.py         # tool definitions
├── data/
│   ├── pdfs/              # put your course PDFs here
│   └── chroma_db/         # ChromaDB persists here automatically
├── quiz_history/          # JSON files, one per session
└── outputs/
```

### PDF files to use
You need at least 2–3 PDFs for meaningful testing. Use your own course notes, or grab any of these free textbooks that work well for AI students:

- *Deep Learning* (Goodfellow et al.) — https://www.deeplearningbook.org — free PDF
- *Speech and Language Processing* (Jurafsky & Martin) — https://web.stanford.edu/~jurafsky/slp3/ — free PDF
- Any of your NUST SEECS course notes — these actually work best since you know the material and can verify the answers

---

## Day 1 — Embeddings From First Principles (4 hrs)

**Goal:** understand what an embedding actually is and build intuition for vector similarity before touching ChromaDB.

Since you have ML background, this will move fast — but don't skip it. The mistakes people make in RAG almost always trace back to not understanding what the embedding is actually capturing.

### What an embedding is (and what it isn't)

An embedding is a fixed-size vector of floats that represents the *semantic meaning* of a piece of text. The key properties:

- Texts with similar meaning have vectors that are close together in the high-dimensional space
- The distance between vectors is meaningful — you can rank documents by how relevant they are to a query
- The embedding model decides what "similar meaning" means — and different models encode similarity differently

What it is NOT: a lossless encoding of the text. You cannot reconstruct the original text from an embedding. It's a compression that preserves semantic relationships and discards everything else.

### Build intuition with raw code before using ChromaDB

```python
# Day 1 exercise: 00_embeddings_raw.py
# Run this and study the output. Don't skip the print statements.

from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
# First run downloads ~90MB. After that, instant.

# ── Step 1: What does an embedding look like? ─────────────────────────────
text = "The attention mechanism in transformers allows the model to focus on relevant parts of the input."
embedding = model.encode(text)

print(f"Input text: {text}")
print(f"Embedding shape: {embedding.shape}")      # (384,) — 384 floats
print(f"First 10 values: {embedding[:10].round(4)}")
print(f"Vector magnitude: {np.linalg.norm(embedding):.4f}")  # ~1.0 (unit vector)

# ── Step 2: Cosine similarity — the core operation of RAG retrieval ───────
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

pairs = [
    (
        "What is backpropagation?",
        "Backpropagation is the algorithm used to compute gradients in neural networks.",
        "SHOULD be high — same topic"
    ),
    (
        "What is backpropagation?",
        "The Eiffel Tower was built in 1889 in Paris.",
        "SHOULD be low — completely unrelated"
    ),
    (
        "How does gradient descent work?",
        "Backpropagation is the algorithm used to compute gradients in neural networks.",
        "SHOULD be medium — related but not identical"
    ),
    (
        "neural network training",
        "training a neural net",          # same meaning, different words
        "SHOULD be very high — paraphrase"
    ),
    (
        "bank",                            # financial institution
        "river bank",                      # physical bank
        "SHOULD be medium — word ambiguity (embeddings capture context poorly for single words)"
    ),
]

print("\n── Cosine Similarity Tests ────────────────────────────────────")
for text_a, text_b, expectation in pairs:
    emb_a = model.encode(text_a)
    emb_b = model.encode(text_b)
    score = cosine_similarity(emb_a, emb_b)
    print(f"\n{expectation}")
    print(f"  A: {text_a}")
    print(f"  B: {text_b}")
    print(f"  Similarity: {score:.4f}")

# ── Step 3: Query vs document — the asymmetry to understand ──────────────
# Queries are short, documents are long. The embedding model handles both
# but they live in different "regions" of the vector space.
# This is why some RAG systems use separate query and document encoders.

query = "explain attention"
documents = [
    "The attention mechanism computes a weighted sum of value vectors.",
    "Self-attention allows each position to attend to all positions.",
    "Multi-head attention runs attention in parallel across h heads.",
    "Convolutional neural networks use local receptive fields.",    # unrelated
    "The softmax function converts logits to probabilities.",       # related but different concept
]

query_emb = model.encode(query)
doc_embs = model.encode(documents)

scores = [cosine_similarity(query_emb, d) for d in doc_embs]
ranked = sorted(zip(scores, documents), reverse=True)

print("\n── Ranked Retrieval ────────────────────────────────────────────")
print(f"Query: '{query}'")
for rank, (score, doc) in enumerate(ranked, 1):
    print(f"  #{rank} ({score:.4f}): {doc}")
```

**Run this, then answer these questions before moving on:**
1. What is the shape of the embedding? What does the 384 mean?
2. Did the "bank" vs "river bank" similarity match your expectation? Why or why not?
3. Which of the 5 documents ranked highest for "explain attention"? Is that the right answer?
4. If you change the query to "what is softmax?", which document ranks highest now?

---

## Day 2 — Chunking Strategy (4 hrs)

**Goal:** understand why chunking is the hardest and most consequential part of RAG, and implement three strategies with measurable quality differences between them.

### Why chunking is the real work in RAG

The context window is limited. You cannot embed and retrieve an entire 300-page textbook at query time — you embed *chunks* of it, retrieve the most relevant chunks, and inject those into the context.

The chunk size decision is a fundamental tradeoff:

| Chunk size | Retrieval behavior | Problem |
|---|---|---|
| Too small (50 tokens) | Very precise, retrieves specific sentences | Retrieved text lacks context — a sentence about "the gradient" is meaningless without surrounding explanation |
| Too large (2000 tokens) | Lots of context in each chunk | One chunk dominates the context window; subtle matches get buried in noise |
| Just right (~300 tokens with overlap) | Good balance | Still depends on the document structure |

There is no universally "right" chunk size. You tune it per document type and query style. That said, **300–400 tokens with 50–100 token overlap** is a reasonable default for textbook-style content.

### Three chunking strategies — implement all three, compare outputs

```python
# ingestion/chunker.py
import re
import tiktoken
from dataclasses import dataclass
from typing import Iterator

@dataclass
class Chunk:
    text: str
    metadata: dict    # source file, page number, chunk index, strategy used
    
    @property
    def token_count(self) -> int:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(self.text))


# ── Strategy 1: Fixed-size token chunking ────────────────────────────────
# Simplest approach. Splits on token boundaries, not sentence boundaries.
# Fast and predictable. Bad at preserving sentence structure.

def chunk_fixed_size(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
    source: str = "unknown"
) -> list[Chunk]:
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    
    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        
        chunks.append(Chunk(
            text=chunk_text.strip(),
            metadata={
                "source": source,
                "chunk_index": idx,
                "strategy": "fixed_size",
                "token_count": len(chunk_tokens)
            }
        ))
        
        # Overlap: next chunk starts `overlap` tokens before the end of this one
        start = end - overlap
        idx += 1
    
    return [c for c in chunks if len(c.text.strip()) > 20]  # drop tiny fragments


# ── Strategy 2: Sentence-aware chunking ──────────────────────────────────
# Groups complete sentences up to chunk_size tokens.
# Never cuts a sentence in half. Much better for question answering.

def chunk_by_sentences(
    text: str,
    chunk_size: int = 300,
    overlap_sentences: int = 1,
    source: str = "unknown"
) -> list[Chunk]:
    enc = tiktoken.get_encoding("cl100k_base")
    
    # Split on sentence endings (handle abbreviations crudely)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_sentences = []
    current_tokens = 0
    idx = 0
    
    for sentence in sentences:
        sentence_tokens = len(enc.encode(sentence))
        
        if current_tokens + sentence_tokens > chunk_size and current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(Chunk(
                text=chunk_text,
                metadata={
                    "source": source,
                    "chunk_index": idx,
                    "strategy": "sentence_aware",
                    "sentence_count": len(current_sentences),
                    "token_count": current_tokens
                }
            ))
            idx += 1
            # Overlap: keep last N sentences for context continuity
            current_sentences = current_sentences[-overlap_sentences:]
            current_tokens = sum(len(enc.encode(s)) for s in current_sentences)
        
        current_sentences.append(sentence)
        current_tokens += sentence_tokens
    
    # Don't forget the last chunk
    if current_sentences:
        chunks.append(Chunk(
            text=" ".join(current_sentences),
            metadata={
                "source": source,
                "chunk_index": idx,
                "strategy": "sentence_aware",
                "sentence_count": len(current_sentences),
                "token_count": current_tokens
            }
        ))
    
    return chunks


# ── Strategy 3: Structure-aware chunking ─────────────────────────────────
# Splits on headers/sections first, then applies sentence chunking within.
# Best for textbooks and structured documents with clear section headings.

def chunk_by_structure(
    text: str,
    chunk_size: int = 350,
    source: str = "unknown"
) -> list[Chunk]:
    # Split on markdown-style headers or numbered sections
    header_pattern = r'\n(?=(?:\d+\.|\#{1,3}|\n[A-Z][A-Z\s]{4,}\n))'
    sections = re.split(header_pattern, text)
    
    all_chunks = []
    for section in sections:
        if not section.strip():
            continue
        # Apply sentence chunking within each section
        section_chunks = chunk_by_sentences(section, chunk_size=chunk_size, source=source)
        all_chunks.extend(section_chunks)
    
    # Re-index
    for i, chunk in enumerate(all_chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["strategy"] = "structure_aware"
    
    return all_chunks
```

### Compare the three strategies on real text

```python
# compare_chunking.py — run this and read the diff
from ingestion.chunker import chunk_fixed_size, chunk_by_sentences, chunk_by_structure

sample_text = """
Backpropagation is the algorithm used to train neural networks by computing 
gradients of the loss function with respect to each weight. The key insight 
is the chain rule of calculus, which allows gradients to flow backwards 
through the network.

The forward pass computes predictions layer by layer. During the backward 
pass, gradients are propagated from the output back to the input. Each 
layer receives a gradient from the layer above it and passes a gradient 
to the layer below.

Gradient Descent

Once gradients are computed, weights are updated using gradient descent. 
The learning rate controls how large each update step is. Too large a 
learning rate causes overshooting. Too small a learning rate causes 
slow convergence or getting stuck in local minima.

Stochastic gradient descent computes gradients on a random mini-batch 
of samples rather than the full dataset. This introduces noise that 
can actually help escape poor local minima.
"""

for strategy_fn in [chunk_fixed_size, chunk_by_sentences, chunk_by_structure]:
    chunks = strategy_fn(sample_text, source="test")
    print(f"\n{'='*50}")
    print(f"Strategy: {chunks[0].metadata['strategy']}")
    print(f"Number of chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i} ({chunk.token_count} tokens):")
        print(f"  '{chunk.text[:120]}...'")
```

**Study the output and answer:**
1. Which strategy cuts sentences in half? When does that create a retrieval problem?
2. The structure-aware strategy found "Gradient Descent" as a section boundary. What would happen if the PDF text doesn't have clear section headers?
3. If a student asks "what is the learning rate?", which strategy produces the best chunk to retrieve? Why?

---

## Day 3 — ChromaDB + The Full Ingestion Pipeline (4 hrs)

**Goal:** embed your chunks and store them in ChromaDB, then query the collection and actually see what gets retrieved.

### What ChromaDB is and isn't

ChromaDB is a local vector database. It stores vectors + associated metadata + the original text, and lets you query by similarity. It persists to disk automatically. There's no server to run, no setup beyond `pip install chromadb`.

What it isn't: a production database. For Week 3 it's perfect. By Week 6 (when you're building the actual Recruitment Agent or Social Media Manager), you might look at Qdrant or Pinecone — but start here.

### PDF text extraction

```python
# ingestion/loader.py
from pypdf import PdfReader
from pathlib import Path
import re

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Returns a list of dicts: {page_number, text, source}
    Extracts per-page so chunk metadata can include page numbers.
    """
    reader = PdfReader(pdf_path)
    source = Path(pdf_path).stem
    pages = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        
        # Clean up common PDF extraction artifacts
        text = re.sub(r'\n{3,}', '\n\n', raw_text)      # collapse excess newlines
        text = re.sub(r'(?<=[a-z])-\n(?=[a-z])', '', text)  # rejoin hyphenated line-breaks
        text = re.sub(r'[ \t]+', ' ', text)               # normalize whitespace
        text = text.strip()
        
        if len(text) > 50:  # skip blank or near-blank pages
            pages.append({
                "page_number": page_num,
                "text": text,
                "source": source,
                "filepath": str(pdf_path)
            })
    
    return pages
```

### Ingestion pipeline — embed and store

```python
# ingestion/embedder.py
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from ingestion.loader import extract_text_from_pdf
from ingestion.chunker import chunk_by_structure, chunk_by_sentences, Chunk
from pathlib import Path
import hashlib
import json

# ChromaDB persists to disk at this path
CHROMA_PATH = "data/chroma_db"

def get_collection(collection_name: str = "study_notes") -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}   # use cosine similarity
    )
    return collection


def chunk_id(chunk: Chunk) -> str:
    """Deterministic ID so re-ingesting the same file doesn't create duplicates."""
    content = f"{chunk.metadata['source']}_{chunk.metadata['chunk_index']}_{chunk.text[:50]}"
    return hashlib.md5(content.encode()).hexdigest()


def ingest_pdf(
    pdf_path: str,
    collection_name: str = "study_notes",
    chunking_strategy: str = "structure"
) -> dict:
    """
    Full pipeline: PDF → pages → chunks → embeddings → ChromaDB
    Returns a summary of what was ingested.
    """
    print(f"Ingesting: {pdf_path}")
    collection = get_collection(collection_name)
    
    # Step 1: Extract text per page
    pages = extract_text_from_pdf(pdf_path)
    print(f"  Extracted {len(pages)} pages")
    
    # Step 2: Chunk each page
    all_chunks = []
    for page in pages:
        if chunking_strategy == "structure":
            chunks = chunk_by_structure(page["text"], source=page["source"])
        else:
            chunks = chunk_by_sentences(page["text"], source=page["source"])
        
        # Add page number to each chunk's metadata
        for chunk in chunks:
            chunk.metadata["page_number"] = page["page_number"]
            chunk.metadata["filepath"] = page["filepath"]
        
        all_chunks.extend(chunks)
    
    print(f"  Created {len(all_chunks)} chunks")
    
    # Step 3: Deduplicate against what's already in the collection
    existing_ids = set(collection.get()["ids"])
    new_chunks = [c for c in all_chunks if chunk_id(c) not in existing_ids]
    
    if not new_chunks:
        print("  All chunks already in collection — nothing to add.")
        return {"ingested": 0, "skipped": len(all_chunks)}
    
    # Step 4: Add to ChromaDB in batches (ChromaDB has a batch size limit)
    batch_size = 100
    for i in range(0, len(new_chunks), batch_size):
        batch = new_chunks[i:i + batch_size]
        collection.add(
            ids=[chunk_id(c) for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch]
        )
        print(f"  Added batch {i//batch_size + 1}: {len(batch)} chunks")
    
    print(f"  Done. Ingested {len(new_chunks)} new chunks.")
    return {
        "ingested": len(new_chunks),
        "skipped": len(all_chunks) - len(new_chunks),
        "total_in_collection": collection.count()
    }


def ingest_directory(pdf_dir: str = "data/pdfs") -> None:
    """Ingest all PDFs in a directory."""
    pdfs = list(Path(pdf_dir).glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}")
        return
    
    for pdf in pdfs:
        result = ingest_pdf(str(pdf))
        print(f"Result: {result}\n")
```

### Build and test the retriever

```python
# retrieval/retriever.py
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from ingestion.embedder import get_collection
from dataclasses import dataclass

@dataclass
class RetrievedChunk:
    text: str
    metadata: dict
    similarity_score: float   # 0.0 to 1.0, higher = more similar
    
    def to_context_string(self) -> str:
        source = self.metadata.get("source", "unknown")
        page = self.metadata.get("page_number", "?")
        return f"[Source: {source}, p.{page} | Relevance: {self.similarity_score:.2f}]\n{self.text}"


def retrieve(
    query: str,
    collection_name: str = "study_notes",
    n_results: int = 5,
    min_similarity: float = 0.3   # filter out low-quality matches
) -> list[RetrievedChunk]:
    """
    Embed the query and retrieve the most similar chunks from ChromaDB.
    """
    collection = get_collection(collection_name)
    
    if collection.count() == 0:
        return []
    
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )
    
    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        # ChromaDB returns cosine distance (0 = identical, 2 = opposite)
        # Convert to similarity score (1 = identical, 0 = opposite)
        similarity = 1 - (distance / 2)
        
        if similarity >= min_similarity:
            chunks.append(RetrievedChunk(
                text=doc,
                metadata=meta,
                similarity_score=similarity
            ))
    
    return sorted(chunks, key=lambda x: x.similarity_score, reverse=True)


def build_context(chunks: list[RetrievedChunk], max_tokens: int = 2000) -> str:
    """
    Join retrieved chunks into a context string that fits within a token budget.
    Most relevant chunks go first; we stop before hitting the budget.
    """
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    
    context_parts = []
    total_tokens = 0
    
    for chunk in chunks:
        chunk_text = chunk.to_context_string()
        chunk_tokens = len(enc.encode(chunk_text))
        
        if total_tokens + chunk_tokens > max_tokens:
            break  # Stop before exceeding budget
        
        context_parts.append(chunk_text)
        total_tokens += chunk_tokens
    
    return "\n\n---\n\n".join(context_parts)
```

### Test the full pipeline before building the agent

```python
# test_pipeline.py — run this end to end before Day 4
from ingestion.embedder import ingest_pdf
from retrieval.retriever import retrieve, build_context

# Ingest one PDF
ingest_pdf("data/pdfs/your_notes.pdf")

# Run test queries and see what comes back
test_queries = [
    "What is the chain rule in backpropagation?",
    "How does the attention mechanism work?",
    "What are the advantages of batch normalization?",
]

for query in test_queries:
    print(f"\nQuery: {query}")
    chunks = retrieve(query, n_results=3)
    print(f"Retrieved {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  ({chunk.similarity_score:.3f}) {chunk.text[:100]}...")
    print(f"\nContext string:\n{build_context(chunks)[:500]}...")
```

**Before moving to Day 4, verify:**
- At least 3 queries return chunks with similarity > 0.4
- The retrieved chunks are actually relevant to the query (read them, don't just check the score)
- If nothing comes back above 0.3, your PDF text extraction probably failed — print the raw extracted text and check for garbage characters

---

## Day 4 — Memory: Short-Term and Long-Term (3 hrs)

**Goal:** implement two distinct memory systems and understand when each applies.

### The two memory problems

**Problem 1 — Short-term (within a session):** you have a conversation with the agent and each follow-up question should build on the previous exchange. This is conversation history — you already built this in Week 1. The new challenge is that long conversations overflow the context window.

**Problem 2 — Long-term (across sessions):** the agent should remember that you got "gradient descent" questions wrong last Tuesday and should quiz you on it again today. This can't live in the context window — it has to be stored on disk.

```python
# memory/conversation.py
import tiktoken
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = "openrouter/owl-alpha"

class ConversationMemory:
    """
    Sliding window with summarization.
    
    Keeps the last N messages verbatim. When the history grows beyond
    a token budget, the oldest messages are summarized into a single
    'memory block' that replaces them.
    """
    
    def __init__(self, max_tokens: int = 3000, keep_last_n: int = 6):
        self.max_tokens = max_tokens
        self.keep_last_n = keep_last_n
        self.messages: list[dict] = []
        self.summary: str = ""   # compressed memory of older turns
        self._enc = tiktoken.get_encoding("cl100k_base")
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._maybe_compress()
    
    def _token_count(self) -> int:
        total = len(self._enc.encode(self.summary))
        for msg in self.messages:
            total += len(self._enc.encode(msg["content"]))
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
            f"{m['role'].upper()}: {m['content']}" for m in to_compress
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
```

```python
# memory/user_state.py
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

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
        # Needs review if accuracy < 70% and has been quizzed at least twice
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
    
    def get_weak_topics(self, min_quizzes: int = 2) -> list[TopicRecord]:
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
    
    def save(self, path: str = "quiz_history/user_state.json"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            "user_id": self.user_id,
            "total_sessions": self.total_sessions,
            "last_session": self.last_session,
            "topics": {k: asdict(v) for k, v in self.topics.items()}
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, user_id: str, path: str = "quiz_history/user_state.json") -> "UserState":
        if not Path(path).exists():
            return cls(user_id=user_id)
        with open(path) as f:
            data = json.load(f)
        state = cls(user_id=data["user_id"])
        state.total_sessions = data.get("total_sessions", 0)
        state.last_session = data.get("last_session")
        for topic_name, record_data in data.get("topics", {}).items():
            state.topics[topic_name] = TopicRecord(**record_data)
        return state
```

---

## Day 5–6 — Full Study Buddy Agent (7 hrs)

### Tool Schemas

```python
# tools/schemas.py  (add to existing file or create new)
STUDY_BUDDY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": (
                "Search the ingested study notes for content relevant to a topic or question. "
                "Returns the most relevant passages from the user's actual documents. "
                "Always call this before answering any content question — "
                "do not rely on general training knowledge alone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic or question to search for. Be specific."
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of passages to retrieve. Default 4, max 8.",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": (
                "Generate quiz questions on a specific topic from the user's notes. "
                "Use this when the user asks to be tested or quizzed. "
                "Always retrieve relevant material first with search_notes before generating questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to quiz on"
                    },
                    "question_type": {
                        "type": "string",
                        "enum": ["multiple_choice", "short_answer", "true_false"],
                        "description": "Format of quiz questions"
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Difficulty level"
                    },
                    "n_questions": {
                        "type": "integer",
                        "description": "Number of questions to generate. Default 3.",
                        "default": 3
                    }
                },
                "required": ["topic", "question_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_quiz_result",
            "description": (
                "Record whether the user answered a quiz question correctly. "
                "Call this after the user responds to each quiz question. "
                "This updates their long-term performance record."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "correct": {"type": "boolean"}
                },
                "required": ["topic", "correct"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weak_topics",
            "description": (
                "Get a list of topics the user has struggled with in past sessions. "
                "Use this at the start of a session to suggest what to review, "
                "or when generating an adaptive quiz."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    }
]
```

### The Agent

```python
# agents/study_buddy.py
import os, json
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from retrieval.retriever import retrieve, build_context
from memory.conversation import ConversationMemory
from memory.user_state import UserState
from tools.schemas import STUDY_BUDDY_TOOLS

load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
MODEL = "openrouter/owl-alpha"
console = Console()

SYSTEM_PROMPT_TEMPLATE = """
You are a personalized study assistant. You help students understand their course material 
by answering questions, explaining concepts, and running adaptive quizzes.

USER PROFILE:
{user_profile}

RULES:
1. When answering content questions, ALWAYS call search_notes first and base your answer 
   on what you retrieve. If the notes don't cover something, say so clearly rather than 
   guessing from general knowledge.
2. When the user asks to be quizzed, call generate_quiz. After they answer, evaluate 
   their response and call record_quiz_result.
3. At the start of the session, call get_weak_topics if the user has history, 
   and suggest reviewing those topics.
4. When citing information, mention the source document and page number from the retrieved chunk.
5. Adjust your explanation depth based on what the user profile says about their weak areas.
"""

def run_study_session(user_id: str = "default"):
    user_state = UserState.load(user_id)
    user_state.total_sessions += 1
    
    conv_memory = ConversationMemory(max_tokens=3000)
    
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        user_profile=user_state.get_summary_for_agent()
    )
    
    # Active quiz state — track what question is currently open
    active_quiz: dict | None = None
    
    def dispatch_tool(tool_name: str, args: dict) -> str:
        nonlocal active_quiz
        
        if tool_name == "search_notes":
            chunks = retrieve(
                args["query"],
                n_results=args.get("n_results", 4)
            )
            if not chunks:
                return "No relevant content found in the study notes for this query."
            context = build_context(chunks, max_tokens=2000)
            return f"Retrieved {len(chunks)} passages:\n\n{context}"
        
        elif tool_name == "generate_quiz":
            # First retrieve relevant material
            chunks = retrieve(args["topic"], n_results=5)
            if not chunks:
                return f"No notes found on '{args['topic']}'. Cannot generate questions."
            
            context = build_context(chunks, max_tokens=1500)
            difficulty = args.get("difficulty", "medium")
            q_type = args["question_type"]
            n = args.get("n_questions", 3)
            
            # Ask the model to generate questions from the retrieved context
            quiz_prompt = (
                f"Based ONLY on this material:\n\n{context}\n\n"
                f"Generate {n} {difficulty} {q_type} questions about {args['topic']}. "
                "Format as JSON array: "
                '[{"question": "...", "answer": "...", "explanation": "..."}]'
                "\nReturn ONLY the JSON array, no other text."
            )
            
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": quiz_prompt}]
            )
            
            raw = response.choices[0].message.content or "[]"
            try:
                # Strip markdown code fences if present
                raw = raw.strip().strip("```json").strip("```").strip()
                questions = json.loads(raw)
                active_quiz = {"topic": args["topic"], "questions": questions, "current": 0}
                return json.dumps(questions, indent=2)
            except json.JSONDecodeError:
                return f"Generated questions (raw):\n{raw}"
        
        elif tool_name == "record_quiz_result":
            user_state.record_quiz_result(args["topic"], args["correct"])
            user_state.save()
            accuracy = user_state.topics[args["topic"]].accuracy
            return (
                f"Recorded: {'correct ✅' if args['correct'] else 'incorrect ❌'} "
                f"for topic '{args['topic']}'. "
                f"Running accuracy on this topic: {accuracy:.0%}"
            )
        
        elif tool_name == "get_weak_topics":
            weak = user_state.get_weak_topics()
            if not weak:
                return "No weak topics identified yet."
            lines = [f"- {t.topic}: {t.accuracy:.0%} accuracy ({t.times_quizzed} attempts)"
                     for t in sorted(weak, key=lambda x: x.accuracy)]
            return "Topics needing review:\n" + "\n".join(lines)
        
        return f"Unknown tool: {tool_name}"
    
    def agent_turn(user_message: str) -> str:
        conv_memory.add("user", user_message)
        messages = conv_memory.get_messages_for_api(system_prompt)
        
        for _ in range(15):
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=2048,
                tools=STUDY_BUDDY_TOOLS,
                messages=messages
            )
            
            msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "stop":
                conv_memory.add("assistant", msg.content or "")
                return msg.content or ""
            
            if finish_reason == "tool_calls":
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": msg.tool_calls
                })
                
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = dispatch_tool(tc.function.name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
        
        return "Something went wrong — max tool iterations hit."
    
    # ── REPL ──────────────────────────────────────────────────────────────
    console.print("\n[bold green]Study Buddy[/bold green] — type 'quit' to exit\n")
    
    # Kick off with a greeting that uses the user profile
    opening = agent_turn("Hello! I'm starting a new study session.")
    console.print(Markdown(opening))
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break
        
        response = agent_turn(user_input)
        console.print(Markdown(f"\n**Agent:** {response}"))
    
    user_state.last_session = __import__("datetime").datetime.now().isoformat()
    user_state.save()
    console.print("\n[dim]Session saved. Goodbye![/dim]")


if __name__ == "__main__":
    run_study_session()
```

### Test conversation sequence

Run these in a single session to exercise all code paths:

```
Turn 1: "Hello! What topics do I have weak spots in?"
Turn 2: "Explain how backpropagation works."           ← should search_notes, cite source
Turn 3: "Can you explain that more simply?"            ← should use conversation memory
Turn 4: "Quiz me on backpropagation with 3 medium multiple choice questions."
Turn 5: [answer the first question — give a wrong answer]
Turn 6: [answer the second question — give a correct answer]
Turn 7: "What did I get wrong just now?"               ← tests conversation memory
Turn 8: "What topics should I focus on next session?"  ← should use get_weak_topics + search
```

Then quit, re-run the agent, and check:
- Does it remember your weak topics from the previous session?
- Does Turn 1 now return the topic you got wrong?

---

## Day 7 — RAG Failure Modes + Reflection (2 hrs)

Understanding where RAG breaks is as important as knowing how to build it. This day documents the failure modes so you recognize them in Week 4+ when your agents produce wrong answers.

### The six RAG failure modes — test each one

**Failure 1 — Retrieval miss:** the right chunk exists but doesn't get retrieved.
```
# Test: ask a question using different terminology than the notes use
# Notes say "gradient descent". Ask about "weight update rule."
# Does retrieval find the right chunk?
```
Fix: query expansion — generate 2–3 reformulations of the query and retrieve for all of them.

**Failure 2 — Context stuffing:** you retrieve too many chunks and the model can't find the signal in the noise.
```
# Test: set n_results=10, ask a very specific question.
# Does the answer quality drop vs n_results=4?
```
Fix: reduce n_results, increase min_similarity threshold.

**Failure 3 — Chunk boundary problem:** the answer spans two adjacent chunks but only one is retrieved.
```
# Test: ask a question whose answer is "a concept introduced on one page and
# explained on the next page" — retrieval gets one page but not the other.
```
Fix: increase chunk overlap, or use larger chunks.

**Failure 4 — Hallucination on retrieved context:** the model uses the retrieved chunks as a springboard and adds details that aren't there.
```
# Test: ask about a topic that's barely mentioned in the notes.
# Does the model extrapolate beyond what was retrieved?
```
Fix: tighten the system prompt — "only use information explicitly present in the retrieved passages."

**Failure 5 — Stale retrieval:** the model ignores the retrieved context and answers from its training data instead.
```
# Test: ask a question about your specific notes ("what does Professor X say about Y?")
# Does the model answer from the retrieved text or from general knowledge?
```
Fix: explicitly label retrieved content in the prompt ("The following is from the user's notes:").

**Failure 6 — Similarity ≠ Relevance:** high cosine similarity doesn't mean the chunk answers the question.
```
# Test: ask "what is wrong with batch normalization?"
# The most similar chunks might discuss batch normalization positively.
# Semantic similarity doesn't capture negation or contrast well.
```
Fix: reranking — retrieve more candidates than you need, then use a second model pass to rerank by actual relevance.

### REFLECTIONS.md questions

1. **Chunking impact.** Run the same 5 queries against both `chunk_fixed_size` and `chunk_by_sentences` ingested collections. Do the top-1 retrieved chunks differ? Does the answer quality differ? Write down the result concretely.

2. **Memory compression.** Have a 10-turn conversation. After the conversation, print `conv_memory.summary`. Does it capture the key information from the compressed turns? What did it lose? Is what it lost important?

3. **The cold start problem.** On session 1, the agent has no quiz history. On session 5, it does. How does the behavior change? Is the session 5 behavior actually better, or just different?

4. **When is RAG the wrong tool?** Describe two scenarios where you would NOT use RAG — where a different approach (fine-tuning, few-shot prompting, a lookup table) would be better. Be specific about why RAG fails in those cases.

5. **Token budget arithmetic.** In your Study Buddy agent, the context window contains: system prompt + memory summary + conversation history + retrieved chunks + the current user message. Estimate the token count of each component for a mid-session query. How close are you to the model's context limit? What breaks first when you exceed it?

---

## Resources Reference Card

| Resource | URL | Cost |
|---|---|---|
| ChromaDB docs | https://docs.trychroma.com | Free |
| sentence-transformers model hub | https://www.sbert.net/docs/pretrained_models.html | Free |
| Anthropic Contextual Retrieval blog | https://www.anthropic.com/news/contextual-retrieval | Free |
| tiktoken (token counting) | https://github.com/openai/tiktoken | Free |
| RAG survey paper (good overview) | https://arxiv.org/abs/2312.10997 | Free |

---

## End-of-Week Checklist

- [ ] I can explain what an embedding is and what cosine similarity measures — without using the phrase "semantic meaning" as a black box
- [ ] I can describe the tradeoff between small chunks (precise retrieval, no context) and large chunks (context-rich, noisy retrieval)
- [ ] My ingestion pipeline handles re-ingestion without creating duplicate chunks
- [ ] My retriever returns a `similarity_score` and I know what score threshold separates useful from useless results for my documents
- [ ] My Study Buddy agent cites which document and page number it retrieved an answer from
- [ ] After a session ends, quiz results are saved to disk and visible on the next session
- [ ] I can trigger and identify at least 3 of the 6 RAG failure modes in my own system
- [ ] I've answered all 5 REFLECTIONS.md questions in writing
- [ ] I understand why conversation memory needs compression and what is lost in that compression

## What Week 4 Builds On This

Week 4 is multi-agent orchestration — the Recruitment Agent. The RAG pipeline from this week becomes the CV-parsing and JD-matching backbone of that system. The memory system becomes the candidate tracking system. The concepts are the same; what changes is that multiple specialized agents use them in a coordinated pipeline rather than a single agent using them in a conversation loop.
