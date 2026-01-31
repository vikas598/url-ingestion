from datetime import datetime, timezone
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
