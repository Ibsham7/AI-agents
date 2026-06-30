from sentence_transformers import SentenceTransformer
from ingestion.loader import extract_text_from_pdf
from ingestion.chunker import chunk_by_structure, chunk_by_sentences, Chunk
from pathlib import Path
import hashlib
from database.pinecone_client import get_pinecone_index

# Initialize the embedding model globally so it's loaded once
model = SentenceTransformer('all-MiniLM-L6-v2')

def chunk_id(chunk: Chunk, pdf_path: str) -> str:
    """Deterministic ID so re-ingesting the same file doesn't create duplicates."""
    page = chunk.metadata.get('page_number', 'unknown')
    content = f"{pdf_path}_p{page}_{chunk.metadata['chunk_index']}_{chunk.text[:50]}"
    return hashlib.md5(content.encode()).hexdigest()

def ingest_pdf(
    pdf_path: str,
    user_id: str,
    document_id: str,
    chunking_strategy: str = "structure"
) -> dict:
    """
    Full pipeline: PDF → pages → chunks → embeddings → Pinecone
    Returns a summary of what was ingested.
    """
    print(f"Ingesting: {pdf_path} for User: {user_id}")
    index = get_pinecone_index()
    if index is None:
        raise Exception("Pinecone index not initialized.")
    
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
            chunk.metadata["user_id"] = user_id
            chunk.metadata["document_id"] = document_id
            chunk.metadata["text"] = chunk.text # Store text in metadata to retrieve it later
        
        all_chunks.extend(chunks)
    
    print(f"  Created {len(all_chunks)} chunks")
    
    if not all_chunks:
        return {"ingested": 0, "skipped": 0}
        
    # Step 3: Embed and Add to Pinecone in batches
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [c.text for c in batch]
        embeddings = model.encode(texts).tolist()
        
        vectors = []
        for j, chunk in enumerate(batch):
            vectors.append({
                "id": chunk_id(chunk, pdf_path),
                "values": embeddings[j],
                "metadata": chunk.metadata
            })
            
        index.upsert(vectors=vectors)
        print(f"  Added batch {i//batch_size + 1}: {len(batch)} chunks")
    
    print(f"  Done. Ingested {len(all_chunks)} new chunks into Pinecone.")
    return {
        "ingested": len(all_chunks)
    }