import requests
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (MillexScraper/1.0)"
}

TIMEOUT = 15


def fetch_page(url: str) -> BeautifulSoup:
    """
    Fetch a collection page and return a BeautifulSoup object.
    """
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def parse_product_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract ONLY UI-visible product URLs from the Millex collection grid.
    """
    urls = set()

    # Updated to be more robust: find any link containing /products/
    # This avoids dependency on specific grid classes (like div.grid__item)
    for link in soup.select("a[href*='/products/']"):
        href = link.get("href")
        if not href:
            continue

        # Normalize URL (remove query params)
        href = href.split("?")[0]
        
        # Avoid collecting the collection page itself or other non-product pages if any
        if href.strip("/") == "products":
             continue

        full_url = urljoin(base_url, href)
        urls.add(full_url)

    return list(urls)


def fetch_collection_products(collection_url: str) -> Dict[str, List[str]]:
    """
    Fetch all UI-visible product URLs from a Millex collection page,
    handling pagination (?page=1, ?page=2, ...).
    """
    product_urls = set()
    page = 1

    MAX_PAGES = 50
    while page <= MAX_PAGES:
        print(f"Scanning page {page}...", end="\r")
        page_url = f"{collection_url}?page={page}"
        try:
            soup = fetch_page(page_url)
        except Exception as e:
            print(f"\nError fetching page {page}: {e}")
            break

        found_urls = parse_product_urls(
            soup=soup,
            base_url=collection_url
        )

        if not found_urls:
            break
            
        # Check if we found any *new* URLs that we haven't seen before
        # This prevents infinite loops if nav/footer links are repeated on every page
        new_urls = set(found_urls) - product_urls
        if not new_urls:
            break

        product_urls.update(new_urls)
        page += 1
    
    print(f"\nFinished scanning. Total unique products found: {len(product_urls)}")

    return {
        "collection_url": collection_url,
        "total_products": len(product_urls),
        "product_urls": sorted(product_urls)
    }


if __name__ == "__main__":
    data = fetch_collection_products("https://millex.in/collections/all")
    print(f"Total products: {data['total_products']}")
    for url in data["product_urls"]:
        print(url)
