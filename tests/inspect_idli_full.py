
import json
from pathlib import Path

META_PATH = Path("d:/inowix/millex/app/services/recommender_system/vector_store/products_meta.json")

def inspect_metadata():
    with open(META_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for p in data:
        if "Millet Rava Idli Instant Mix - 400g" in p.get("title", ""):
            print("--- FOUND SINGLE IDLI MIX ---")
            print(f"ID: {p.get('product_id')}")
            print(f"Title: {p.get('title')}")
            print(f"Type: {p.get('product_type')}")
            print(f"Availability: {p.get('availability')}")
            print(f"Description: {p.get('description')}")
            print("-----------------------------")

if __name__ == "__main__":
    inspect_metadata()
