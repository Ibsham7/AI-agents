from dataclasses import dataclass
from database.pinecone_client import get_pinecone_index
from sentence_transformers import SentenceTransformer

# Initialize the embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

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
    user_id: str,
    n_results: int = 5,
    min_similarity: float = 0.65   # filter out low-quality matches
) -> list[RetrievedChunk]:
    """
    Embed the query and retrieve the most similar chunks from Pinecone for a specific user.
    """
    index = get_pinecone_index()
    if index is None:
        print("Pinecone index not initialized.")
        return []
    
    query_embedding = model.encode(query).tolist()
    
    response = index.query(
        vector=query_embedding,
        top_k=n_results,
        include_metadata=True,
        filter={
            "user_id": {"$eq": user_id}
        }
    )
    
    chunks = []
    for match in response.matches:
        similarity = match.score
        if similarity >= min_similarity:
            chunks.append(RetrievedChunk(
                text=match.metadata.get("text", ""),
                metadata=match.metadata,
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