from app.services.ai.query_understanding import extract_query_intent
import json

def test_intent():
    # Test 1: Single
    msg1 = "I want idli mix"
    res1 = extract_query_intent(msg1, history=[])
    print(f"\nQuery: '{msg1}'")
    print(f"Filter: {res1.get('product_type_filter')}")
    print(f"Rewritten: {res1.get('rewritten_query')}")

    # Test 2: Combo
    msg2 = "Show me combos"
    # Simulate history where previous was idli
    hist = [{"role": "user", "content": "I want idli mix"}, {"role": "assistant", "content": "Here is idli mix..."}]
    res2 = extract_query_intent(msg2, history=hist)
    print(f"\nQuery: '{msg2}'")
    print(f"Filter: {res2.get('product_type_filter')}")
    print(f"Rewritten: {res2.get('rewritten_query')}")

if __name__ == "__main__":
    test_intent()
