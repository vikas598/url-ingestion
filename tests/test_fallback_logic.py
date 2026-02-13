
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.recommender_system.search_service import search_products, load_resources

def test_fallback_logic():
    print("Loading resources...")
    load_resources()
    
    query = "idli"
    print(f"\n--- Testing Fallback Logic for '{query}' ---")
    
    # 1. Initial Search (Single)
    products = search_products(query, k=3, product_type="single")
    print(f"Initial 'single' search returned {len(products)} products.")
    
    # 2. Match Counting
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    print(f"Keywords: {keywords}")
    
    valid_matches = 0
    for p in products:
        p_text = (p.get('title', '') + ' ' + str(p.get('category', ''))).lower()
        if any(kw in p_text for kw in keywords):
            valid_matches += 1
            print(f"Match found: {p['title']}")
    
    print(f"Valid matches: {valid_matches}")
    
    # 3. Fallback Trigger
    if valid_matches < 2:
        print("Creating Fallback...")
        expanded_products = search_products(query, k=3, product_type="any")
        
        expanded_matches = 0
        for p in expanded_products:
            p_text = (p.get('title', '') + ' ' + str(p.get('category', ''))).lower()
            if any(kw in p_text for kw in keywords):
                expanded_matches += 1
                print(f"Expanded Match: {p['title']}")
        
        print(f"Expanded matches: {expanded_matches}")
        
        if expanded_matches > valid_matches:
            print("SUCCESS: Fallback would be triggered and improve results.")
        else:
            print("FAILURE: Fallback would not improve results.")
    else:
        print("Fallback NOT triggered (Enough matches found).")

if __name__ == "__main__":
    test_fallback_logic()
