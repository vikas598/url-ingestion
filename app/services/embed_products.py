import json
import faiss
from pathlib import Path
from embedding_utils import embed_texts
# Import products and pre-formatted text from json_to_text.py
from json_to_text import products, product_texts

# Paths
VECTOR_STORE = Path("vector_store")
VECTOR_STORE.mkdir(exist_ok=True)

INDEX_PATH = VECTOR_STORE / "products.index"
META_PATH = VECTOR_STORE / "products_meta.json"

# 🔑 SAME embedding function
print("Generating embeddings...")
embeddings = embed_texts(product_texts)

# Create FAISS index (exact search)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save
faiss.write_index(index, str(INDEX_PATH))

with open(META_PATH, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2)

print("✅ Product embeddings created and stored")
