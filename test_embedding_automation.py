import json
import shutil
from pathlib import Path
from app.services.recommender_system.embed_products import generate_product_embeddings
from app.services.recommender_system.search_service import load_resources

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data/processed"
VECTOR_STORE = BASE_DIR / "vector_store"

print(f"Test running in: {BASE_DIR}")
print(f"Processed dir: {PROCESSED_DIR}")
print(f"Exists: {PROCESSED_DIR.exists()}")

# Backup existing data
BACKUP_DIR = BASE_DIR / "data_backup_temp"

def setup():
    print("Setting up test environment...")
    if PROCESSED_DIR.exists():
        # Try to clear but log errors
        try:
            shutil.copytree(PROCESSED_DIR, BACKUP_DIR / "processed", dirs_exist_ok=True)
            for f in PROCESSED_DIR.glob("*"):
                if f.is_file():
                    try:
                        print(f"Deleting {f.name}...")
                        f.unlink()
                    except Exception as e:
                        print(f"⚠️ Failed to delete {f.name}: {e}")
        except Exception as e:
            print(f"⚠️ Clean setup failed: {e}")
    else:
        PROCESSED_DIR.mkdir(parents=True)

def teardown():
    print("\nRestoring environment...")
    # Clear test data
    for f in PROCESSED_DIR.glob("*.json"):
        f.unlink()
    
    # Restore backup
    if (BACKUP_DIR / "processed").exists():
        for f in (BACKUP_DIR / "processed").glob("*.json"):
            shutil.copy2(f, PROCESSED_DIR)
        shutil.rmtree(BACKUP_DIR)
    
    # Trigger regeneration with original data to restore index
    print("Restoring original index...")
    generate_product_embeddings()

def create_test_data():
    p1 = {
        "product_id": "test_1",
        "source_url": "http://test.com/1",
        "title": "Test Product 1",
        "pricing": {"price": 100}
    }
    p2 = {
        "product_id": "test_2",
        "source_url": "http://test.com/2",
        "title": "Test Product 2",
        "pricing": {"price": 200}
    }
    
    with open(PROCESSED_DIR / "test1.json", "w") as f:
        json.dump([p1], f)
        
    with open(PROCESSED_DIR / "test2.json", "w") as f:
        json.dump({"products": [p2]}, f) # Test dict wrapper format

def run_test():
    try:
        setup()
        create_test_data()
        
        print("\n--- Testing Embedding Generation ---")
        count = generate_product_embeddings()
        
        assert count == 2, f"Expected 2 products, got {count}"
        print("✅ Correct product count")
        
        # Verify metadata file
        with open(VECTOR_STORE / "products_meta.json", "r") as f:
            meta = json.load(f)
            # Filter valid IDs (legacy data might miss product_id)
            ids = [p.get("product_id") for p in meta if p.get("product_id")]
            
            assert "test_1" in ids and "test_2" in ids
            print(f"✅ Metadata contains test products. Total indexed: {len(meta)}")
            
        print("\n--- Testing Search Service Reload ---")
        load_resources(force=True)
        print("✅ resources loaded without error")

    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        teardown()

if __name__ == "__main__":
    run_test()
