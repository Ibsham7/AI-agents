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
    if strategy_fn == chunk_fixed_size:
        chunks = strategy_fn(sample_text, chunk_size=50, overlap=10, source="test")
    else:
        chunks = strategy_fn(sample_text, chunk_size=50, source="test")
    print(f"\n{'='*50}")
    print(f"Strategy: {chunks[0].metadata['strategy']}")
    print(f"Number of chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i} ({chunk.token_count} tokens):")
        print(f"  '{chunk.text}'")