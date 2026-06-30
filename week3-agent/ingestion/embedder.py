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
        embedding_function=embedding_fn, # type: ignore
        metadata={"hnsw:space": "cosine"}   # use cosine similarity
    )
    return collection


def chunk_id(chunk: Chunk) -> str:
    """Deterministic ID so re-ingesting the same file doesn't create duplicates."""
    page = chunk.metadata.get('page_number', 'unknown')
    content = f"{chunk.metadata['source']}_p{page}_{chunk.metadata['chunk_index']}_{chunk.text[:50]}"
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