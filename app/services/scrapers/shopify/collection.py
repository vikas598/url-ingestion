import requests
import time
from app.core.exceptions import APIException

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (URL-Ingestor/1.0)",
    "Accept": "application/json"
}

TIMEOUT = 5
MAX_RETRIES = 3
PAGE_LIMIT = 250
RATE_LIMIT_DELAY = 1  # seconds


def fetch_collection_products(store_url: str, collection_handle: str) -> list:
    """
    Fetch ALL products from a Shopify collection using public JSON endpoint.
    """
    all_products = []
    page = 1

    while True:
        url = (
            f"{store_url}/collections/"
            f"{collection_handle}/products.json"
            f"?limit={PAGE_LIMIT}&page={page}"
        )

        last_exception = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    headers=DEFAULT_HEADERS,
                    timeout=TIMEOUT
                )

                if response.status_code == 403:
                    raise APIException("SHOPIFY_COLLECTION_BLOCKED")

                if response.status_code == 404:
                    raise APIException("COLLECTION_NOT_FOUND")

                if response.status_code >= 500:
                    last_exception = APIException("SCRAPER_FAILED")
                    continue

                if response.status_code != 200:
                    raise APIException("SCRAPER_FAILED")

                data = response.json()

                if "products" not in data:
                    raise APIException("NOT_SHOPIFY_COLLECTION")

                products = data["products"]

                if not products:
                    return all_products

                all_products.extend(products)
                break

            except requests.exceptions.Timeout:
                last_exception = APIException("SCRAPER_TIMEOUT")

            except requests.exceptions.RequestException:
                last_exception = APIException("SCRAPER_NETWORK_ERROR")

        else:
            if last_exception:
                raise last_exception

        page += 1
        time.sleep(RATE_LIMIT_DELAY)
