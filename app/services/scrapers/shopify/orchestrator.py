from app.services.scrapers.shopify.collections import fetch_collections
from app.services.scrapers.shopify.collection import fetch_collection_products
from app.services.processor import process_shopify_product
from app.services.storage import store_product


def scrape_shopify_store(store_url: str, limit_collections: int = 1) -> dict:
    collections = fetch_collections(store_url)

    if limit_collections:
        collections = collections[:limit_collections]

    products_seen = set()
    stored_count = 0

    for col in collections:
        handle = col["handle"]
        products = fetch_collection_products(store_url, handle)

        for product in products:
            product_id = product["id"]

            # dedup across collections
            if product_id in products_seen:
                continue

            products_seen.add(product_id)

            # 🔁 REUSE EXISTING PIPELINE
            processed = process_shopify_product(
                raw_data={"product": product},
                source_url=store_url
            )

            store_product(
                product_id=processed["product_id"],
                product_data=processed
            )

            stored_count += 1

    return {
        "store": store_url,
        "collections_scraped": len(collections),
        "products_scraped": stored_count
    }
