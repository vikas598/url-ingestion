from urllib.parse import urlparse, urlunparse
import requests

from app.core.exceptions import APIException


def build_shopify_json_url(product_url: str) -> str:
    """
    Validates Shopify product URL and converts it to .json endpoint.
    """

    # --- Parse URL ---
    parsed = urlparse(product_url)

    if not parsed.scheme or not parsed.netloc:
        raise APIException("INVALID_URL_FORMAT")

    # --- Normalize path ---
    path = parsed.path.rstrip("/")

    # Must be a product page
    if "/products/" not in path:
        raise APIException("NOT_A_PRODUCT_URL")

    # Remove query params & fragments
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        "",
        "",
        ""
    ))

    json_url = f"{normalized}.json"

    # --- Validate JSON endpoint ---
    try:
        response = requests.get(json_url, timeout=5)
    except requests.exceptions.Timeout:
        raise APIException("SCRAPER_TIMEOUT")
    except requests.exceptions.RequestException:
        raise APIException("SCRAPER_NETWORK_ERROR")

    if response.status_code == 403:
        raise APIException("SHOPIFY_JSON_BLOCKED")

    if response.status_code == 404:
        raise APIException("PRODUCT_NOT_FOUND")

    if response.status_code != 200:
        raise APIException("SCRAPER_FAILED")

    # Must be valid Shopify product JSON
    try:
        data = response.json()
    except Exception:
        raise APIException("NOT_SHOPIFY_PRODUCT")

    if "product" not in data:
        raise APIException("NOT_SHOPIFY_PRODUCT")

    return json_url
