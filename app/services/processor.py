from datetime import datetime, timezone
from bs4 import BeautifulSoup
from app.core.exceptions import APIException


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
            "category": _extract_categories(description_clean),  # Extract categories from description
            
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

def _extract_categories(description: str) -> list[str]:
    """
    Extract categories from product description based on keywords.
    
    Rules:
    - ready-to-cook: contains "instant mix"
    - health-mix: contains "health drink mix"
    - infant-food: contains "baby"
    
    Args:
        description: Cleaned product description text
        
    Returns:
        List of matching category slugs
    """
    if not description:
        return []
    
    desc_lower = description.lower()
    categories = []
    
    if "instant mix" in desc_lower:
        categories.append("ready-to-cook")
        
    if "health drink mix" in desc_lower:
        categories.append("health-mix")
        
    if "baby" in desc_lower:
        categories.append("infant-food")
        
    return categories
