import json
import os
from typing import List
from app.core.exceptions import APIException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "products")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def _extract_product_id(product_data: dict) -> str:
    """
    Extract product ID from scraped product data.
    Supports both Millex and Shopify product formats.
    """
    # Try explicit product_id field (Shopify normalized format)
    if "product_id" in product_data:
        return str(product_data["product_id"])
    
    # Try Shopify raw format
    if "id" in product_data:
        return str(product_data["id"])
    
    # Try handle field
    if "handle" in product_data:
        return product_data["handle"]
    
    # Extract from URL (Millex format: https://millex.in/products/product-name)
    if "url" in product_data:
        url = product_data["url"]
        
        # Remove query parameters if present (e.g., ?variant=12345)
        if '?' in url:
            url = url.split('?')[0]
        
        # Extract the last path segment as the product ID
        parts = url.rstrip('/').split('/')
        if len(parts) > 0:
            return parts[-1]
    
    raise ValueError("Unable to extract product ID from product data")


def store_product_data(product_data: dict) -> str:
    """
    Store a single product to JSON file.
    Automatically extracts product ID from the product data.
    Returns the file path where the product was stored.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        
        product_id = _extract_product_id(product_data)
        file_path = os.path.join(DATA_DIR, f"{product_id}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

        return file_path

    except Exception as e:
        raise APIException("STORAGE_FAILURE") from e


def store_products(products: List[dict]) -> List[str]:
    """
    Store multiple products to JSON files.
    Returns a list of file paths where products were stored.
    """
    file_paths = []
    
    for product_data in products:
        try:
            file_path = store_product_data(product_data)
            file_paths.append(file_path)
        except Exception as e:
            # Log error but continue with other products
            print(f"Failed to store product: {e}")
            continue
    
    return file_paths


def store_collection(collection_url: str, products: List[dict]) -> str:
    """
    Store an entire collection of products in a single JSON file.
    File is named based on the collection URL and timestamp.
    Returns the file path where the collection was stored.
    """
    try:
        from datetime import datetime
        from urllib.parse import urlparse
        
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Extract collection name from URL
        # e.g., https://millex.in/collections/all -> all
        # or https://millex.in -> homepage
        parsed = urlparse(collection_url)
        path_parts = parsed.path.rstrip('/').split('/')
        
        # Determine filename based on URL
        if '/collections/' in collection_url:
            collection_name = path_parts[-1] if path_parts else 'collection'
        else:
            # Homepage or other page
            collection_name = 'homepage'
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{collection_name}_{timestamp}.json"
        file_path = os.path.join(DATA_DIR, filename)
        
        # Create collection data structure
        collection_data = {
            "collection_url": collection_url,
            "scraped_at": datetime.now().isoformat(),
            "product_count": len(products),
            "products": products
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        return file_path

    except Exception as e:
        raise APIException("STORAGE_FAILURE") from e


# Legacy function for backward compatibility
def store_product(product_id: str, product_data: dict) -> str:
    """
    Legacy storage function. Use store_product_data() instead.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)

        file_path = os.path.join(DATA_DIR, f"{product_id}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)

        return file_path

    except Exception:
        raise APIException("STORAGE_FAILURE")


def store_processed_product(product_data: dict, product_id: str = None) -> str:
    """
    Store processed (cleaned & normalized) product data to JSON file.
    
    Args:
        product_data: Processed product data from processor
        product_id: Optional product ID (extracted if not provided)
        
    Returns:
        File path where processed product was stored
    """
    try:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        
        # Extract product ID from source URL if not provided
        if not product_id:
            source_url = product_data.get("source_url", "")
            if source_url:
                parts = source_url.rstrip('/').split('/')
                product_id = parts[-1].split('?')[0]  # Remove query params
            else:
                import uuid
                product_id = str(uuid.uuid4())
        
        file_path = os.path.join(PROCESSED_DIR, f"{product_id}.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=2)
        
        return file_path
        
    except Exception as e:
        raise APIException("STORAGE_FAILURE") from e


def store_processed_collection(collection_url: str, products: List[dict]) -> str:
    """
    Store processed collection of products in a single JSON file.
    
    Args:
        collection_url: URL of collection/homepage
        products: List of processed product data
        
    Returns:
        File path where processed collection was stored
    """
    try:
        from datetime import datetime
        from urllib.parse import urlparse
        
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        
        # Extract name from URL
        parsed = urlparse(collection_url)
        path_parts = parsed.path.rstrip('/').split('/')
        
        if '/collections/' in collection_url:
            name = path_parts[-1] if path_parts else 'collection'
        else:
            name = 'homepage'
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_processed_{timestamp}.json"
        file_path = os.path.join(PROCESSED_DIR, filename)
        
        # Create structure
        collection_data = {
            "collection_url": collection_url,
            "processed_at": datetime.now().isoformat(),
            "product_count": len(products),
            "products": products
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)
        
        return file_path
        
    except Exception as e:
        raise APIException("STORAGE_FAILURE") from e
