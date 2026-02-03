import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from urllib.parse import urlparse

from app.services.scrapers.shopify.html.currency import extract_store_currency


HEADERS = {
    "User-Agent": "Mozilla/5.0 (MillexScraper/1.0)"
}


def scrape_millex_product(product_url: str) -> Dict[str, Any]:
    """
    Scrape a single Millex product page.
    HTML-first, site-specific (millex.in).
    """

    html = _fetch_html(product_url)
    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    description = _extract_description(soup)
    images = _extract_images(soup)
    price_info = _extract_price(html, soup)
    availability = _extract_availability(soup)

    domain = urlparse(product_url).netloc
    currency = extract_store_currency(html, domain)

    # ✅ SSR-safe variant extraction
    variants = extract_variants(soup)

    result = {
        "url": product_url,
        "title": title,
        "currency": currency,
        "description_html": description,
        "images": images,
        "availability": availability,
        "variants": variants,
    }
    
    # Add price fields based on what was extracted
    if price_info:
        result.update(price_info)
    
    return result


# ---------------- helpers ---------------- #

def _fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.text


def _extract_title(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else None


def _extract_description(soup: BeautifulSoup) -> str | None:
    for details in soup.find_all("details"):
        summary = details.find("summary")
        if summary and "description" in summary.get_text(strip=True).lower():
            content = details.find("div", class_=re.compile(r"accordion__?content"))
            if content:
                return str(content)
    return None


def _extract_images(soup: BeautifulSoup) -> list[str]:
    images = []
    for img in soup.select("img"):
        src = img.get("src")
        if src and "cdn.shopify.com" in src:
            images.append(src)
    return list(set(images))


def _extract_price(html: str, soup: BeautifulSoup) -> Dict[str, float] | None:
    """
    Extract price information from product page.
    Returns dict with either:
    - {'price': float} for regular price
    - {'original_price': float, 'current_price': float} for sale price
    """
    
    # First try LD+JSON for structured data
    product_json = _extract_from_ld_json(html)
    price_from_json = _extract_price_from_js(product_json)
    
    # Check if product has a sale price in HTML
    price_sale_el = soup.select_one("div.price__sale")
    
    if price_sale_el:
        # Product is on sale - extract both original and current price
        original_price = None
        current_price = None
        
        # Original price is in <s> tag (strikethrough)
        compare_el = price_sale_el.select_one("s.price-item--regular")
        if compare_el:
            original_price = _parse_price_text(compare_el.get_text(strip=True))
        
        # Current/sale price is in span.price-item--sale
        sale_el = price_sale_el.select_one("span.price-item--sale")
        if sale_el:
            current_price = _parse_price_text(sale_el.get_text(strip=True))
        
        # Return sale pricing if we got both values
        if original_price and current_price and original_price > current_price:
            return {
                "original_price": original_price,
                "current_price": current_price
            }
    
    # Not on sale - try to get regular price
    if price_from_json is not None:
        return {"price": price_from_json}
    
    # Fallback to HTML extraction
    price_regular_el = soup.select_one("div.price__regular")
    if price_regular_el:
        price_item = price_regular_el.select_one("span.price-item")
        if price_item:
            price = _parse_price_text(price_item.get_text(strip=True))
            if price:
                return {"price": price}
    
    return None


def _parse_price_text(text: str) -> float | None:
    """
    Extract numeric price from text like 'Rs. 399.00' or '₹249.00'
    """
    if not text:
        return None
    
    try:
        # Strategy: find all sequences of digits with optional decimal point
        # This handles cases like "Rs. 249.00" or "Rs.249.00" or "249.00"
        # Match one or more digits, optionally followed by a decimal point and more digits
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1))
    except (ValueError, AttributeError):
        pass
    
    return None


def _extract_from_ld_json(html: str) -> list[Dict[str, Any]] | None:
    soup = BeautifulSoup(html, "html.parser")
    data = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data.append(json.loads(script.get_text(strip=True)))
        except Exception:
            continue

    return data or None


def _extract_price_from_js(json_data: list[Dict[str, Any]] | None) -> float | None:
    if not json_data:
        return None

    for item in json_data:
        if item.get("@type") == "Product":
            offers = item.get("offers")
            
            # Handle single offer (dict)
            if isinstance(offers, dict):
                try:
                    return float(offers.get("price"))
                except (TypeError, ValueError):
                    pass
            
            # Handle multiple offers (list) - take the first/lowest price
            elif isinstance(offers, list) and len(offers) > 0:
                try:
                    # Get prices from all offers and return the minimum
                    prices = []
                    for offer in offers:
                        if isinstance(offer, dict) and "price" in offer:
                            prices.append(float(offer["price"]))
                    
                    if prices:
                        return min(prices)
                except (TypeError, ValueError):
                    pass
    
    return None


def _extract_availability(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ").lower()
    return not ("out of stock" in text or "sold out" in text)


# ---------------- VARIANTS (SSR SAFE) ---------------- #

def extract_variants(soup: BeautifulSoup) -> list[dict]:
    """
    Extract variants from server-rendered <input data-*> attributes.
    Works with requests (no JS execution).
    """

    variants = []

    for input_el in soup.select("input[type='radio'][data-variant-title]"):
        variant_id = input_el.get("data-variant-id") or input_el.get("value")
        title = input_el.get("data-variant-title")
        available = input_el.get("data-variant-available") == "true"

        price_raw = input_el.get("data-variant-price")
        compare_raw = input_el.get("data-variant-compare-price")

        price = float(price_raw) / 100 if price_raw else None
        compare_price = float(compare_raw) / 100 if compare_raw else None

        variant = {
            "variant_id": variant_id,
            "title": title,
            "available": available,
        }

        if compare_price and compare_price > price:
            variant["current_price"] = price
            variant["original_price"] = compare_price
            variant["savings_text"] = "Discounted"
        else:
            variant["price"] = price
            variant["savings_text"] = "Standard price"

        variants.append(variant)

    return variants
