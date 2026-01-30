import requests
from app.core.exceptions import APIException

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (URL-Ingestor/1.0)",
    "Accept": "application/json"
}

TIMEOUT = 5
MAX_RETRIES = 3


def fetch_collections(store_url: str) -> list[dict]:
    """
    Fetch all Shopify collections using public collections.json endpoint.
    Returns raw collection objects.
    """
    url = f"{store_url}/collections.json"
    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=TIMEOUT
            )

            if response.status_code == 403:
                raise APIException("SHOPIFY_COLLECTIONS_BLOCKED")

            if response.status_code >= 500:
                last_exception = APIException("SCRAPER_FAILED")
                continue

            if response.status_code != 200:
                raise APIException("SCRAPER_FAILED")

            data = response.json()

            if "collections" not in data:
                raise APIException("NOT_SHOPIFY_STORE")

            return data["collections"]

        except requests.exceptions.Timeout:
            last_exception = APIException("SCRAPER_TIMEOUT")

        except requests.exceptions.RequestException:
            last_exception = APIException("SCRAPER_NETWORK_ERROR")

    if last_exception:
        raise last_exception

    raise APIException("SCRAPER_FAILED")
