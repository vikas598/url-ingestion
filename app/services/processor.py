from datetime import datetime, timezone
from bs4 import BeautifulSoup
from app.core.exceptions import APIException


def process_shopify_product(raw_data: dict, source_url: str) -> dict:
    """
    Normalize a single Shopify product JSON into internal schema.
    NOTE:
    - This function is PURE.
    - No HTML fetching.
    - No currency inference.
    - Enrichment happens AFTER this step.
    """
    try:
        product = raw_data["product"]

        variants = []
        prices = []

        for v in product.get("variants", []):
            price = float(v.get("price", 0))
            prices.append(price)

            variants.append({
                "variant_id": str(v.get("id")),
                "title": v.get("title"),
                "price": price,
                "available": v.get("available", False),
                "sku": v.get("sku")
            })

        images = []
        for img in product.get("images", []):
            images.append({
                "url": img.get("src"),
                "alt_text": img.get("alt")
            })

        now = datetime.now(timezone.utc).isoformat()

        return {
            "schema_version": "1.0",
            "product_id": str(product.get("id")),
            "source": "shopify",
            "source_url": source_url,
            "handle": product.get("handle"),
            "title": product.get("title"),
            "vendor": product.get("vendor"),
            "product_type": product.get("product_type"),
            "description": product.get("body_html", ""),

            # currency intentionally left empty
            "pricing": {
                "currency": None,
                "min_price": min(prices) if prices else None,
                "max_price": max(prices) if prices else None
            },

            "variants": variants,
            "images": images,

            "availability": {
                "in_stock": any(v["available"] for v in variants),
                "total_variants": len(variants),
                "available_variants": sum(1 for v in variants if v["available"])
            },

            "metadata": {
                "created_at": product.get("created_at"),
                "ingested_at": now
            }
        }

    except Exception as exc:
        raise APIException("PROCESSING_ERROR") from exc


def process_millex_product(raw_data: dict) -> dict:
    """
    Clean and normalize Millex scraped product data.
    
    Processing steps:
    - Clean HTML from description
    - Normalize pricing data
    - Standardize variant format
    - Extract metadata
    - Add ingestion timestamp
    
    Args:
        raw_data: Raw product data from Millex scraper
        
    Returns:
        Normalized product data with cleaned fields
    """
    try:
        # Clean description HTML
        description_html = raw_data.get("description_html", "")
        description_clean = _clean_html_description(description_html)
        
        # Extract pricing info
        variants = raw_data.get("variants", [])
        prices = [v.get("price", 0) for v in variants if v.get("price") is not None]
        
        # Normalize variants
        normalized_variants = []
        for v in variants:
            normalized_variants.append({
                "variant_id": str(v.get("variant_id", "")),
                "title": v.get("title"),
                "price": float(v.get("price", 0)),
                "available": v.get("available", False),
                "savings_text": v.get("savings_text")
            })
        
        # Normalize images
        images = []
        for img_url in raw_data.get("images", []):
            images.append({
                "url": img_url,
                "alt_text": None  # Millex doesn't provide alt text
            })
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Extract product_id from URL
        url = raw_data.get("url", "")
        product_id = ""
        if url:
            # Remove query parameters
            url_clean = url.split('?')[0]
            # Extract last segment
            product_id = url_clean.rstrip('/').split('/')[-1]

        return {
            "schema_version": "1.0",
            "source": "millex",
            "product_id": product_id,  # Added product_id
            "source_url": url,
            
            "title": raw_data.get("title"),
            "description": description_clean,
            "description_html": description_html,  # Keep original for reference
            
            "pricing": {
                "currency": raw_data.get("currency", "INR"),
                "price": raw_data.get("price")
            },
            
            "variants": normalized_variants,
            "images": images,
            
            "availability": {
                "in_stock": raw_data.get("availability", False),
                "total_variants": len(normalized_variants),
                "available_variants": sum(1 for v in normalized_variants if v["available"])
            },
            
            "metadata": {
                "ingested_at": now,
                "variant_count": len(normalized_variants)
            }
        }
        
    except Exception as exc:
        raise APIException("PROCESSING_ERROR") from exc


def _clean_html_description(html: str) -> str:
    """
    Remove HTML tags and clean text from description.
    
    Args:
        html: HTML string from product description
        
    Returns:
        Clean plain text
    """
    if not html:
        return ""
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get text with spaces between elements
        text = soup.get_text(separator=' ')
        
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        
        return text
    except Exception:
        # If cleaning fails, return original
        return html
