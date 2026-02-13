import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from urllib.parse import urlparse, urljoin

from app.services.scrapers.millex.utils import extract_store_currency


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
    images = _extract_images(soup)  # ✅ FIXED
    price_info = _extract_price(html, soup)
    availability = _extract_availability(soup)

    domain = urlparse(product_url).netloc
    currency = extract_store_currency(html, domain)

    # SSR-safe variant extraction
    variants = extract_variants(soup)

    product_type = "single"
    if title:
        title_lower = title.lower()
        
        # Multiple patterns for combo detection
        combo_patterns = [
            r"total\s+\d+\s*(?:g|kg|ml)\s*-\s*each\s+\d+\s*(?:g|kg|ml)",  # "Total 800g - each 400g"
            r"buy\s+\d+.*get\s+\d+",  # "Buy 2 Get 1 Free"
            r"pack\s+of\s+\d+",  # "Pack of 3"
            r"set\s+of\s+\d+",  # "Set of 2"
            r"\d+\s*[\+x]\s*\d+",  # "2+1" or "2x500g"
            r"combo",  # Direct combo mention
            r"bundle",  # Bundle products
            r"special\s+offer.*(?:buy|get|\d+)",  # Special offers with quantities
        ]
        
        # Check if title matches any combo pattern
        for pattern in combo_patterns:
            if re.search(pattern, title_lower):
                product_type = "combo"
                break

    result = {
        "url": product_url,
        "title": title,
        "product_type": product_type,
        "currency": currency,
        "description_html": description,
        "images": images,
        "availability": availability,
        "variants": variants,
    }
    
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
    """
    Extract product images from the carousel in correct visual order.
    """
    images: list[str] = []
    seen: set[str] = set()
    base_url = "https://millex.in"

    # STRICT selector → preserves carousel order
    for img in soup.select("div.carousel-cell img"):
        src = img.get("src")
        if not src:
            continue

        full_url = urljoin(base_url, src)

        # hard filter → product images only
        if "/cdn/shop/files/" not in full_url:
            continue

        # preserve order, avoid duplicates
        if full_url not in seen:
            images.append(full_url)
            seen.add(full_url)

    return images


def _extract_price(html: str, soup: BeautifulSoup) -> Dict[str, float] | None:
    """
    Extract price information from product page.
    """
    
    product_json = _extract_from_ld_json(html)
    price_from_json = _extract_price_from_js(product_json)
    
    price_sale_el = soup.select_one("div.price__sale")
    
    if price_sale_el:
        original_price = None
        current_price = None
        
        compare_el = price_sale_el.select_one("s.price-item--regular")
        if compare_el:
            original_price = _parse_price_text(compare_el.get_text(strip=True))
        
        sale_el = price_sale_el.select_one("span.price-item--sale")
        if sale_el:
            current_price = _parse_price_text(sale_el.get_text(strip=True))
        
        if original_price and current_price and original_price > current_price:
            return {
                "original_price": original_price,
                "current_price": current_price
            }
    
    if price_from_json is not None:
        return {"price": price_from_json}
    
    price_regular_el = soup.select_one("div.price__regular")
    if price_regular_el:
        price_item = price_regular_el.select_one("span.price-item")
        if price_item:
            price = _parse_price_text(price_item.get_text(strip=True))
            if price:
                return {"price": price}
    
    return None


def _parse_price_text(text: str) -> float | None:
    if not text:
        return None
    
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    return float(match.group(1)) if match else None


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
            
            if isinstance(offers, dict):
                try:
                    return float(offers.get("price"))
                except (TypeError, ValueError):
                    pass
            
            elif isinstance(offers, list):
                prices = []
                for offer in offers:
                    if isinstance(offer, dict) and "price" in offer:
                        try:
                            prices.append(float(offer["price"]))
                        except (TypeError, ValueError):
                            pass
                if prices:
                    return min(prices)
    
    return None


def _extract_availability(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ").lower()
    return not ("out of stock" in text or "sold out" in text)


# ---------------- VARIANTS (SSR SAFE) ---------------- #

def extract_variants(soup: BeautifulSoup) -> list[dict]:
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

        if compare_price and price and compare_price > price:
            variant["current_price"] = price
            variant["original_price"] = compare_price
            variant["savings_text"] = "Discounted"
        else:
            variant["price"] = price
            variant["savings_text"] = "Standard price"

        variants.append(variant)

    return variants
