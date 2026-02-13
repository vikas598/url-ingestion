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
_last_loaded_ts = 0


def load_resources(force: bool = False) -> bool:
    global _index, _metadata, _last_loaded_ts

    if not INDEX_PATH.exists() or not META_PATH.exists():
        if _last_loaded_ts > 0:
            print("⚠️ Vector store files missing.")
        else:
            print("⚠️ Vector store not found. Run embed_products.py first.")
        return False

    # Check modification times
    try:
        index_mtime = INDEX_PATH.stat().st_mtime
        meta_mtime = META_PATH.stat().st_mtime
        current_ts = max(index_mtime, meta_mtime)
    except OSError:
        return False

    # Reload if forced, not loaded, or stale
    if force or _index is None or _metadata is None or current_ts > _last_loaded_ts:
        try:
            print(f"🔄 Loading vector store (TS: {current_ts})...")
            _index = faiss.read_index(str(INDEX_PATH))
            with open(META_PATH, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
            
            _last_loaded_ts = current_ts
            print(f"✅ Loaded {_index.ntotal} vectors and {len(_metadata)} products.")
            return True

        except Exception as e:
            print(f"❌ Failed to load vector store: {e}")
            _index = None
            _metadata = None
            _last_loaded_ts = 0
            return False
            
    return True


def resolve_category(query: str, memory: dict | None) -> str | None:
    """
    Category priority:
    1. Memory (LLM-confirmed explicit category)
    2. Keyword detection fallback
    """
    if memory and memory.get("category"):
        return memory["category"]

    return detect_category(query)


def search_products(query: str, k: int = 5, memory: dict | None = None, product_type: str = "single"):
    print(f"DEBUG: Entering search_products with query='{query}', type='{product_type}'", flush=True)
    if not query.strip():
        return []

    if not load_resources():
        return []

    keywords = extract_keywords(query)
    resolved_category = resolve_category(query, memory)

    # Embed + normalize query
    query_embedding = embed_texts([query])
    faiss.normalize_L2(query_embedding)

    # Retrieve more candidates than needed (Fetch deep to handle filtering)
    fetch_k = k * 20  # Fetch 20x to ensure we find enough matches after filtering
    scores, indices = _index.search(query_embedding, fetch_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or idx >= len(_metadata):
            continue
            
        if len(results) >= k:
            break

        product = _metadata[idx]

        # 🔹 PRODUCT TYPE FILTER
        preferred_type = memory.get("product_type") if memory else None
        # The original code had a preferred_type from memory.
        # Now we also have a direct product_type argument.
        # We'll prioritize the direct argument if it's not "any", otherwise use memory.
        effective_product_type_filter = product_type
        if effective_product_type_filter == "any" and memory:
            effective_product_type_filter = memory.get("product_type", "any")

        if effective_product_type_filter != "any":
            # FILTER: Product Type
            p_type = product.get('product_type', 'single') # Default to single if missing
            print(f"DEBUG: Found Product: {product.get('title', 'Unknown')} | Type: {p_type} | Filter: {effective_product_type_filter}")
            
            if p_type != effective_product_type_filter:
                continue

        # 🔹 HARD CATEGORY FILTER
        if resolved_category:
            product_categories = product.get("category")

            if isinstance(product_categories, str):
                # Product has a single category string
                if product_categories != resolved_category:
                    continue
            elif isinstance(product_categories, list):
                # Product has a list of categories
                if len(product_categories) > 0:
                    # If product has categories, check if resolved_category is in them
                    if resolved_category not in product_categories:
                        continue
                # else: Product has empty category list [] - allow it through
            # else: Product has no category field or None - allow it through
        
        # 🔹 PRICE FILTERING (New)
        raw_price = product.get("pricing", {}).get("price")
        budget = memory.get("budget") if memory else None
        
        price_penalty = 0.0

        if budget:
            # If product has no price, exclude it to be safe
            if raw_price is None:
                continue
                
            try:
                price = float(raw_price)
                if price > (budget * 1.10):  # Hard limit: Budget + 10%
                    continue
                elif price > budget:         # Soft limit: Budget < Price <= Budget + 10%
                    price_penalty = 0.1      # Apply 10% score penalty
            except (ValueError, TypeError):
                continue

        # 🔹 KEYWORD SOFT BOOST
        product_text = (
            f"{product.get('title','')} "
            f"{product.get('category','')}"
        ).lower()

        keyword_matches = sum(1 for kw in keywords if kw in product_text)
        keyword_score = keyword_matches / max(len(keywords), 1) if keywords else 0.0

        final_score = (0.8 * score) + (0.2 * keyword_score) - price_penalty

        results.append({
            **product,  # Include all product fields (title, images, pricing, variants, etc.)
            "similarity_score": float(final_score)
        })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:k]
