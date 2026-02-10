from pathlib import Path
import json
import faiss
from app.services.recommender_system.embedding_utils import embed_texts
from app.services.recommender_system.keyword_filter import (
    extract_keywords,
    detect_category
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
VECTOR_STORE = BASE_DIR / "vector_store"
INDEX_PATH = VECTOR_STORE / "products.index"
META_PATH = VECTOR_STORE / "products_meta.json"

_index = None
_metadata = None


def load_resources(force: bool = False) -> bool:
    global _index, _metadata

    if _index is not None and _metadata is not None and not force:
        return True

    if not INDEX_PATH.exists() or not META_PATH.exists():
        print("⚠️ Vector store not found. Run embed_products.py first.")
        return False

    try:
        _index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)

        print(f"✅ Loaded {_index.ntotal} vectors and {len(_metadata)} products.")
        return True

    except Exception as e:
        print(f"❌ Failed to load vector store: {e}")
        _index = None
        _metadata = None
        return False


def resolve_category(query: str, memory: dict | None) -> str | None:
    """
    Category priority:
    1. Memory (LLM-confirmed explicit category)
    2. Keyword detection fallback
    """
    if memory and memory.get("category"):
        return memory["category"]

    return detect_category(query)


def search_products(query: str, k: int = 5, memory: dict | None = None):
    if not query.strip():
        return []

    if not load_resources():
        return []

    keywords = extract_keywords(query)
    resolved_category = resolve_category(query, memory)

    # Embed + normalize query
    query_embedding = embed_texts([query])
    faiss.normalize_L2(query_embedding)

    # Retrieve more candidates than needed
    scores, indices = _index.search(query_embedding, k * 3)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or idx >= len(_metadata):
            continue

        product = _metadata[idx]

        # 🔹 HARD CATEGORY FILTER
        if resolved_category:
            product_categories = product.get("category")

            if isinstance(product_categories, str):
                if product_categories != resolved_category:
                    continue
            elif isinstance(product_categories, list):
                if resolved_category not in product_categories:
                    continue
            else:
                continue

        # 🔹 KEYWORD SOFT BOOST
        product_text = (
            f"{product.get('title','')} "
            f"{product.get('category','')}"
        ).lower()

        keyword_matches = sum(1 for kw in keywords if kw in product_text)
        keyword_score = keyword_matches / max(len(keywords), 1) if keywords else 0.0

        final_score = (0.8 * score) + (0.2 * keyword_score)

        results.append({
            "title": product.get("title", ""),
            "source_url": product.get("source_url", ""),
            "category": product.get("category"),
            "similarity_score": float(final_score)
        })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:k]
