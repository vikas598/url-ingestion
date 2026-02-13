
import json
from pathlib import Path

META_PATH = Path("d:/inowix/millex/app/services/recommender_system/vector_store/products_meta.json")

def inspect_metadata():
    with open(META_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    found = False
    for p in data:
        if "Millet Rava Idli Instant Mix - 400g" in p.get("title", ""):
            print("FOUND SINGLE IDLI MIX:")
            print(json.dumps(p, indent=2))
            found = True
            break
            
    if not found:
        print("Single Idli Mix NOT found in metadata file!")

if __name__ == "__main__":
    inspect_metadata()
