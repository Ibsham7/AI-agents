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
    min_similarity: float = 0.65   # filter out low-quality matches (0.5 is mathematically unrelated)
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
        results["documents"][0], # type: ignore
        results["metadatas"][0], # type: ignore
        results["distances"][0]  # type: ignore
    ):
        # ChromaDB returns cosine distance (0 = identical, 2 = opposite)
        # Convert to similarity score (1 = identical, 0 = opposite)
        similarity = 1 - (distance / 2)
        
        if similarity >= min_similarity:
            chunks.append(RetrievedChunk(
                text=doc,
                metadata=meta, # type: ignore
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