
import sys
import os
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.recommender_system.search_service import search_products, load_resources

def test_search():
    print("Loading resources...")
    load_resources()
    
    query = "idli"
    print(f"\n--- Searching for '{query}' with product_type='single' ---")
    results_single = search_products(query, k=5, product_type="single")
    print(f"Found {len(results_single)} results.")
    for p in results_single:
        print(f" - {p['title']} ({p.get('product_type')})")

    print(f"\n--- Searching for '{query}' with product_type='combo' ---")
    results_combo = search_products(query, k=5, product_type="combo")
    print(f"Found {len(results_combo)} results.")
    for p in results_combo:
        print(f" - {p['title']} ({p.get('product_type')})")

    print(f"\n--- Searching for '{query}' with product_type='any' ---")
    results_any = search_products(query, k=5, product_type="any")
    print(f"Found {len(results_any)} results.")
    for p in results_any:
        print(f" - {p['title']} ({p.get('product_type')})")


if __name__ == "__main__":
    import sys
    # Redirect stdout to a file
    with open("reproduce_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        test_search()

