from sentence_transformers import SentenceTransformer
import numpy as np

# Load model ONCE
_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts):
    """
    Accepts:
      - list[str]  → for products
      - list[str]  → for queries (length 1)

    Returns:
      - numpy array of embeddings
    """
    if not isinstance(texts, list):
        raise ValueError("Input must be a list of strings")

    return _model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
