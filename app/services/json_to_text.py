import json
from pathlib import Path

# Get the absolute path to the data directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data/processed"

# Find the latest JSON file
json_files = list(PROCESSED_DIR.glob("*.json"))
if not json_files:
    raise FileNotFoundError(f"No JSON files found in {PROCESSED_DIR}")

# Sort by modification time (newest first) and pick the first one
latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
DATA_PATH = latest_file

print(f"Processing latest file: {DATA_PATH}\n")

# Load JSON
with open(DATA_PATH, "r", encoding="utf-8") as f:
    products = json.load(f)

# Handle both list and dictionary (with "products" key) formats
if isinstance(products, dict):
    products = products.get("products", [])

if not isinstance(products, list):
    raise ValueError("JSON file must contain a LIST of products (or a dict with 'products' key)")

def product_to_text(product: dict) -> str:
    return (
        f"Title: {product.get('title', '')}. "
        f"Description: {product.get('description', '')}. "
        f"Price: {product.get('pricing', {}).get('price', '')}. "
        f"URL: {product.get('source_url', '')}."
    )

# Convert each product to text
product_texts = [product_to_text(p) for p in products]

# Output check
print(f"Total products processed: {len(product_texts)}\n")
print("Sample output:\n")
print(product_texts[0])
