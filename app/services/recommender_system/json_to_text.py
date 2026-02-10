import json
from pathlib import Path
from typing import List, Dict

# Get the absolute path to the data directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data/processed"

def load_all_processed_products() -> List[Dict]:
    """
    Load ALL processed product JSON files from data/processed directory.
    Deduplicate based on product URL/ID if necessary.
    Returns a list of product dictionaries.
    """
    if not PROCESSED_DIR.exists():
        return []

    json_files = list(PROCESSED_DIR.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {PROCESSED_DIR}")
        return []

    print(f"Found {len(json_files)} JSON files to process.")
    for f in json_files:
        print(f" - {f.name}")

    all_products = {}

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Handle different formats (list vs dict wrapper)
                products_list = []
                if isinstance(data, list):
                    products_list = data
                elif isinstance(data, dict) and "products" in data:
                    products_list = data["products"]
                
                for p in products_list:
                    if not isinstance(p, dict):
                        continue
                    # Use source_url or a unique ID as key for deduplication
                    unique_key = p.get("product_id") or p.get("source_url") or p.get("url") or p.get("title")
                    
                    if unique_key:
                        all_products[unique_key] = p
                        
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return list(all_products.values())

def product_to_text(product: dict) -> str:
    """
    Convert a product dictionary to a text string for embedding.
    """
    return (
        f"Title: {product.get('title', '')}. "
        f"Description: {product.get('description', '')}. "
        f"Price: {product.get('pricing', {}).get('price', '')}. "
        f"URL: {product.get('source_url', '')}."
    )

def get_product_texts() -> tuple[List[Dict], List[str]]:
    """
    Helper to get both raw products and their text representations.
    """
    products = load_all_processed_products()
    texts = [product_to_text(p) for p in products]
    return products, texts

if __name__ == "__main__":
    products, texts = get_product_texts()
    print(f"Total unique products loaded: {len(products)}")
    if texts:
        print("Sample text:\n", texts[0])
