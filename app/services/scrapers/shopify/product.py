import requests
from app.core.exceptions import APIException

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (URL-Ingestor/1.0)",
    "Accept": "application/json"
}

TIMEOUT = 5
MAX_RETRIES = 3


def fetch_shopify_product(json_url: str) -> dict:
    """
    Fetch raw Shopify product JSON with retries.
    """

    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                json_url,
                headers=DEFAULT_HEADERS,
                timeout=TIMEOUT
            )

            if response.status_code == 403:
                raise APIException("SHOPIFY_JSON_BLOCKED")

            if response.status_code == 404:
                raise APIException("PRODUCT_NOT_FOUND")

            if response.status_code >= 500:
                last_exception = APIException("SCRAPER_FAILED")
                continue

            if response.status_code != 200:
                raise APIException("SCRAPER_FAILED")

            try:
                data = response.json()
            except Exception:
                raise APIException("NOT_SHOPIFY_PRODUCT")

            if "product" not in data:
                raise APIException("NOT_SHOPIFY_PRODUCT")

            return data

        except requests.exceptions.Timeout:
            last_exception = APIException("SCRAPER_TIMEOUT")

        except requests.exceptions.RequestException:
            last_exception = APIException("SCRAPER_NETWORK_ERROR")

    # retries exhausted
    if last_exception:
        raise last_exception

    raise APIException("SCRAPER_FAILED")
