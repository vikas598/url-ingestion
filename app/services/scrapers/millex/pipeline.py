import time
from typing import List, Dict, Any

from app.services.scrapers.millex.collection import fetch_collection_products
from app.services.scrapers.millex.product import scrape_millex_product



REQUEST_DELAY = 1.0  # seconds (polite scraping)


def run_collection_pipeline(collection_url: str) -> List[Dict[str, Any]]:
    """
    Orchestrates the full Millex scraping pipeline:
    1. Discover UI-visible product URLs from collection
    2. Scrape each product individually
    """

    collection_data = fetch_collection_products(collection_url)
    product_urls = collection_data["product_urls"]

    results: List[Dict[str, Any]] = []
    total = len(product_urls)

    print(f"Discovered {total} products\n")

    for index, product_url in enumerate(product_urls, start=1):
        try:
            print(f"[{index}/{total}] Scraping → {product_url}")

            product_data = scrape_millex_product(product_url)
            results.append(product_data)

            time.sleep(REQUEST_DELAY)

        except Exception as exc:
            print(f"[ERROR] Failed to scrape {product_url}")
            print(f"        Reason: {exc}")

    return results


if __name__ == "__main__":
    products = run_collection_pipeline(
        "https://millex.in/collections/all"
    )

    print(f"\nSuccessfully scraped {len(products)} products")
