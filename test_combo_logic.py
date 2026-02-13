import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_combo_logic():
    session = requests.Session()

    print("\n--- Test 1: 'Idli Mix' (Expect Single + Combo Tip) ---")
    r1 = session.post(f"{BASE_URL}/chat", json={"message": "I want idli mix"})
    data1 = r1.json()
    response1 = data1.get("response", "")
    print(f"AI Response 1: {response1[:200]}...")  # Show start
    
    if "Combo" in response1 or "pack" in response1:
        print("✅ SUCCESS: Upsell tip likely present.")
    else:
        print("⚠️ WARNING: upsell tip missing?")

    print("\n--- Test 2: 'Show me combos' (Expect Combo Products) ---")
    r2 = session.post(f"{BASE_URL}/chat", json={"message": "Show me combos"}) # Uses cookie from r1
    data2 = r2.json()
    response2 = data2.get("response", "")
    products2 = data2.get("products", [])
    
    print(f"Products Found: {len(products2)}")
    if products2:
        print(f"Sample Product: {products2[0].get('product_type', 'unknown')}")
        if products2[0].get('product_type') == 'combo':
            print("✅ SUCCESS: Fetched combo products.")
        else:
            print("❌ FAILED: Did not fetch combo products.")
    else:
        print("❌ FAILED: No products found.")

if __name__ == "__main__":
    test_combo_logic()
