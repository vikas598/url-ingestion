"""
Migration script to fix product_type classifications for existing products.
"""

import json
import re
from pathlib import Path

def detect_product_type(title: str) -> str:
    """
    Detect if a product is a combo or single based on its title.
    Uses the same logic as product.py scraper.
    """
    if not title:
        return "single"
    
    title_lower = title.lower()
    
    # Multiple patterns for combo detection
    combo_patterns = [
        r"total\s+\d+\s*(?:g|kg|ml)\s*-\s*each\s+\d+\s*(?:g|kg|ml)",  # "Total 800g - each 400g"
        r"buy\s+\d+.*get\s+\d+",  # "Buy 2 Get 1 Free"
        r"pack\s+of\s+\d+",  # "Pack of 3"
        r"set\s+of\s+\d+",  # "Set of 2"
        r"\d+\s*[\+x]\s*\d+",  # "2+1" or "2x500g"
        r"combo",  # Direct combo mention
        r"bundle",  # Bundle products
        r"special\s+offer.*(?:buy|get|\d+)",  # Special offers with quantities
    ]
    
    # Check if title matches any combo pattern
    for pattern in combo_patterns:
        if re.search(pattern, title_lower):
            return "combo"
    
    return "single"


def migrate_product_type(data_dir: Path):
    """
    Update product_type field in all JSON files in the data directory.
    """
    if not data_dir.exists():
        print(f"❌ Directory not found: {data_dir}")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print(f"⚠️ No JSON files found in {data_dir}")
        return
    
    print(f"🔍 Found {len(json_files)} JSON files to process")
    
    total_products = 0
    updated_products = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            
            title = data.get('title', '')
            old_type = data.get('product_type', 'single')
            new_type = detect_product_type(title)
            
            if old_type != new_type:
                data['product_type'] = new_type
                
                # Also update in metadata if it exists
                if 'metadata' in data and 'product_type' in data['metadata']:
                    data['metadata']['product_type'] = new_type
                
                modified = True
                updated_products += 1
                print(f"  ✅ {json_file.name}: {old_type} → {new_type}")
                print(f"     Title: {title[:80]}...")
            
            total_products += 1
            
            if modified:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"  ❌ Error processing {json_file.name}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"  Total products processed: {total_products}")
    print(f"  Products updated: {updated_products}")
    print(f"  Products unchanged: {total_products - updated_products}")


if __name__ == "__main__":
    # Path to processed data
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data" / "processed"
    
    print("🚀 Starting product_type migration...")
    print(f"📁 Data directory: {DATA_DIR}")
    print()
    
    migrate_product_type(DATA_DIR)
    
    print("\n✅ Migration complete!")
    print("⚠️ Remember to rebuild the vector index by running:")
    print("   python -m app.services.recommender_system.embed_products")

