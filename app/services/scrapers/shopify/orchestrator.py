from urllib.parse import urlparse

from app.services.scrapers.shopify.collections import fetch_collections
from app.services.scrapers.shopify.collection import fetch_collection_products
from app.services.processor import process_shopify_product
from app.services.storage import store_product

from app.services.scrapers.shopify.html.currency import extract_store_currency
from app.services.http.fetcher import fetch_html   # or wherever you placed fetch_html


def scrape_shopify_store(store_url: str, limit_collections: int = 1) -> dict:
    """
    Orchestrates store-level scraping.
    - Fetches collections
    - Fetches products
    - Processes products (pure)
    - Enriches with store-level currency (HTML, cached)
    - Stores results
    """

    # 1️⃣ Fetch collections
    collections = fetch_collections(store_url)
    if limit_collections:
        collections = collections[:limit_collections]

    products_seen = set()
    stored_count = 0

    # 2️⃣ Fetch ONE product HTML to extract store currency
    # Pick first product URL we encounter
    store_currency = None
    store_domain = urlparse(store_url).netloc
    store_html_fetched = False
    store_html = None

    for col in collections:
        products = fetch_collection_products(store_url, col["handle"])

        for product in products:
            product_id = product["id"]

            # dedup across collections
            if product_id in products_seen:
                continue
            products_seen.add(product_id)

            # 3️⃣ Fetch store HTML ONCE (first product only)
            if not store_html_fetched:
                product_url = f"{store_url}/products/{product['handle']}"
                store_html = fetch_html(product_url)
                store_currency = extract_store_currency(store_html, store_domain)
                store_html_fetched = True

            # 4️⃣ Process product (PURE)
            processed = process_shopify_product(
                raw_data={"product": product},
                source_url=store_url
            )

            # 5️⃣ Enrich with currency (store-level)
            if store_currency and not processed["pricing"]["currency"]:
                processed["pricing"]["currency"] = store_currency

            # 6️⃣ Store product
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
