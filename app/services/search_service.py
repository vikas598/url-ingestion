from pathlib import Path
import json
import faiss
import numpy as np
from app.services.embedding_utils import embed_texts

# Paths
BASE_DIR = Path(__file__).resolve().parent
VECTOR_STORE = BASE_DIR / "vector_store"
INDEX_PATH = VECTOR_STORE / "products.index"
META_PATH = VECTOR_STORE / "products_meta.json"

# Global variables to hold the loaded index and metadata
_index = None
_metadata = []

def load_resources():
    """Loads the FAISS index and metadata if not already loaded."""
    global _index, _metadata
    if _index is None:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            raise FileNotFoundError("Vector store not found. Run embed_products.py first.")
        
        _index = faiss.read_index(str(INDEX_PATH))
        
        with open(META_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)
            
        print(f"✅ Loaded index with {_index.ntotal} vectors and {len(_metadata)} products.")

def search_products(query: str, k: int = 3):
    """
    Searches for the top k most similar products to the query.
    """
    load_resources() # Ensure resources are loaded
    
    # Generate embedding for the query
    # embed_texts expects a list of strings
    query_embedding = embed_texts([query]) 
    
    # Search
    distances, indices = _index.search(query_embedding, k)
    
    # Retrieve results
    results = []
    # indices is a 2D array [[idx1, idx2, ...]]
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(_metadata):
            product = _metadata[idx]
            # Add distance/score if needed, but for now just return the product
            # Faiss L2 distance: lower is better (0 is identical)
            results.append(product)
            
    return results
