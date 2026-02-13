import json
import os
import re

# Determine project root and data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "products")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Regex pattern for combo detection
PATTERN = r"total\s+\d+\s*(?:g|kg|ml)\s*-\s*each\s+\d+\s*(?:g|kg|ml)"

def get_product_type(title):
    if not title:
        return "single"
    if re.search(PATTERN, title, re.IGNORECASE):
        return "combo"
    return "single"

def update_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated = False
        
        # Helper to update a single product dict
        def update_product_dict(p):
            curr = p.get("product_type")
            title = p.get("title")
            new_type = get_product_type(title)
            if curr != new_type:
                p["product_type"] = new_type
                return True
            return False

        # Case 1: Collection / Aggregated file
        if "products" in data and isinstance(data["products"], list):
            print(f"Processing collection file: {os.path.basename(filepath)}")
            for p in data["products"]:
                if update_product_dict(p):
                    updated = True
        
        # Case 2: Individual Product file
        elif "title" in data:
            if update_product_dict(data):
                updated = True
                
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"UPDATED: {os.path.basename(filepath)}")
        else:
            # print(f"SKIPPED: {os.path.basename(filepath)}")
            pass
            
    except Exception as e:
        print(f"ERROR: {filepath} - {e}")

def main():
    print(f"Scanning for product files in:\n - {DATA_DIR}\n - {PROCESSED_DIR}")
    
    count = 0
    # Update raw products
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json") and "collection" not in filename and "homepage" not in filename:
                update_file(os.path.join(DATA_DIR, filename))
                count += 1

    if os.path.exists(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
             if filename.endswith(".json"):
                update_file(os.path.join(PROCESSED_DIR, filename))
                count += 1
                
    print(f"Scanned {count} files.")

if __name__ == "__main__":
    main()
