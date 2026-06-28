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

query = "what is softmax"
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