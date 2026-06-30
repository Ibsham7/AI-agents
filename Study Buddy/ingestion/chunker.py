wimport re
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
    overlap = min(overlap, chunk_size - 1)
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
        
        if end >= len(tokens):
            break
            
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