import json
import faiss
from pathlib import Path
from app.services.recommender_system.embedding_utils import embed_texts
from app.services.recommender_system.json_to_text import get_product_texts


# Paths
BASE_DIR = Path(__file__).resolve().parent
VECTOR_STORE = BASE_DIR / "vector_store"


def generate_product_embeddings() -> int:
    """
    Regenerate embeddings for ALL processed products.
    Uses OpenAI embeddings + FAISS (cosine similarity).
    Saves index and metadata.
    """

    VECTOR_STORE.mkdir(exist_ok=True)

    INDEX_PATH = VECTOR_STORE / "products.index"
    META_PATH = VECTOR_STORE / "products_meta.json"

    # 1. Load product data
    print("Loading product data...")
    products, product_texts = get_product_texts()

    if not products:
        print("No products found to embed.")
        return 0

    # 2. Generate embeddings (OpenAI)
    print(f"Generating embeddings for {len(products)} products...")
    embeddings = embed_texts(product_texts)

    # 3. Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)

    # 4. Create FAISS index (cosine similarity via Inner Product)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # 5. Save index and metadata
    faiss.write_index(index, str(INDEX_PATH))

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"✅ Indexed {len(products)} products.")
    return len(products)


if __name__ == "__main__":
    generate_product_embeddings()
