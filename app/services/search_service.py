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

def load_resources(force: bool = False):
    """Loads the FAISS index and metadata if not already loaded or if force=True."""
    global _index, _metadata
    if _index is None or force:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            # If files don't exist, we can't load them.
            # But we shouldn't crash on import/startup if they are missing.
            print("Vector store not found. Waiting for first scrape...")
            return
        
        try:
            _index = faiss.read_index(str(INDEX_PATH))
            
            with open(META_PATH, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
                
            print(f"✅ Loaded index with {_index.ntotal} vectors and {len(_metadata)} products.")
        except Exception as e:
            print(f"Error loading vector store: {e}")

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
            # Return only requested fields
            filtered_product = {
                "title": product.get("title", ""),
                "source_url": product.get("source_url", "")
            }
            results.append(filtered_product)
            
    return results
