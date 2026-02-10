import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from urllib.parse import urljoin

from app.services.scrapers.millex.product import scrape_millex_product


HEADERS = {
    "User-Agent": "Mozilla/5.0 (MillexScraper/1.0)"
}

REQUEST_DELAY = 1.0  # seconds (polite scraping)


def scrape_homepage_products(homepage_url: str) -> List[Dict[str, Any]]:
    """
    Scrape all products from Millex homepage.
    
    Pipeline:
    1. Extract all product URLs from homepage
    2. Filter out already-scraped products
    3. Scrape each new product individually
    
    Args:
        homepage_url: URL of the homepage to scrape
        
    Returns:
        List of scraped product data dictionaries
    """
    from app.services.dedup import filter_unscraped_urls
    
    # Step 1: Extract product URLs from homepage
    html = _fetch_html(homepage_url)
    soup = BeautifulSoup(html, "html.parser")
    product_urls = _extract_product_urls(soup, homepage_url)
    
    print(f"Discovered {len(product_urls)} products on homepage")
    
    # Step 2: Filter out already-scraped products
    unscraped_urls = filter_unscraped_urls(product_urls)
    skipped_count = len(product_urls) - len(unscraped_urls)
    
    if skipped_count > 0:
        print(f"Skipping {skipped_count} already-scraped products")
    print(f"Scraping {len(unscraped_urls)} new products\n")
    
    # Step 3: Scrape each product
    results: List[Dict[str, Any]] = []
    total = len(unscraped_urls)
    
    for index, product_url in enumerate(unscraped_urls, start=1):
        try:
            print(f"[{index}/{total}] Scraping → {product_url}")
            
            product_data = scrape_millex_product(product_url)
            results.append(product_data)
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as exc:
            print(f"[ERROR] Failed to scrape {product_url}")
            print(f"        Reason: {exc}")
    
    print(f"\nSuccessfully scraped {len(results)} products from homepage")
    return results


def _fetch_html(url: str) -> str:
    """Fetch HTML content from URL"""
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.text


def _extract_product_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract all product URLs from homepage.
    Looks for links containing '/products/' in the href.
    """
    product_links = set()
    
    # Find all links that contain '/products/' in href
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        
        # Check if this is a product link
        if "/products/" in href:
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(base_url, href)
            
            # Remove query parameters and fragments for deduplication
            clean_url = absolute_url.split('?')[0].split('#')[0]
            
            product_links.add(clean_url)
    
    # Return sorted list for consistent ordering
    return sorted(list(product_links))
