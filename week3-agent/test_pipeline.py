import sys
sys.stdout.reconfigure(encoding='utf-8')

from ingestion.embedder import ingest_pdf
from retrieval.retriever import retrieve, build_context

# Ingest one PDF
ingest_pdf("data/pdfs/Prog4AI_W7.pdf")

# Run test queries and see what comes back
test_queries = [
    "What are REST APIs and how do they work?",
    "What is MAAS",
    "What is flask",
    "how to make america great again",
]

for query in test_queries:
    print(f"\nQuery: {query}")
    chunks = retrieve(query, n_results=3)
    print(f"Retrieved {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  ({chunk.similarity_score:.3f}) {chunk.text[:100]}...")
    print(f"\nContext string:\n{build_context(chunks)[:500]}...")