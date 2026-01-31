import re
import json
from typing import Optional
from bs4 import BeautifulSoup

# simple in-memory cache
_STORE_CURRENCY_CACHE: dict[str, str] = {}


def extract_store_currency(html: str, store_domain: str) -> Optional[str]:
    """
    Phase-1 currency extractor for Shopify.
    Tries:
      1) Shopify.currency.active
      2) application/ld+json offers.priceCurrency
    Cached per store.
    """

    # cache first
    if store_domain in _STORE_CURRENCY_CACHE:
        return _STORE_CURRENCY_CACHE[store_domain]

    currency = _from_shopify_currency_js(html) or _from_ld_json(html)

    if currency:
        _STORE_CURRENCY_CACHE[store_domain] = currency

    return currency


def _from_shopify_currency_js(html: str) -> Optional[str]:
    """
    Extract from:
      Shopify.currency = { "active": "USD", ... }
    """
    m = re.search(
        r'Shopify\.currency\s*=\s*{[^}]*"active"\s*:\s*"([A-Z]{3})"',
        html
    )
    return m.group(1) if m else None


def _from_ld_json(html: str) -> Optional[str]:
    """
    Extract from schema.org Product JSON-LD:
      offers.priceCurrency
    """
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            offers = item.get("offers")
            if isinstance(offers, dict):
                cur = offers.get("priceCurrency")
                if cur:
                    return cur

    return None
