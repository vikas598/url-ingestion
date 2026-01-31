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
    price = _extract_price(html, soup)
    availability = _extract_availability(soup)

    domain = urlparse(product_url).netloc
    currency = extract_store_currency(html, domain)

    # ✅ SSR-safe variant extraction
    variants = extract_variants(soup)

    return {
        "url": product_url,
        "title": title,
        "price": price,
        "currency": currency,
        "description_html": description,
        "images": images,
        "availability": availability,
        "variants": variants,
    }


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


def _extract_price(html: str, soup: BeautifulSoup) -> float | None:
    product_json = _extract_from_ld_json(html)
    price = _extract_price_from_js(product_json)
    if price is not None:
        return price

    price_el = soup.select_one("div.price__regular")
    if not price_el:
        return None

    try:
        return float(re.sub(r"[^\d.]", "", price_el.get_text()))
    except ValueError:
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
            if isinstance(offers, dict):
                try:
                    return float(offers.get("price"))
                except Exception:
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
