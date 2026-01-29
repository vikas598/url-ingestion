from fastapi import status

ERRORS = {
    # API / INPUT
    "INVALID_REQUEST_BODY": (status.HTTP_400_BAD_REQUEST, "Request body is missing or invalid"),
    "URL_MISSING": (status.HTTP_400_BAD_REQUEST, "URL field is required"),
    "INVALID_URL_FORMAT": (status.HTTP_400_BAD_REQUEST, "Invalid URL format"),

    # URL HANDLING
    "NOT_A_PRODUCT_URL": (status.HTTP_400_BAD_REQUEST, "URL is not a Shopify product page"),
    "NOT_SHOPIFY_PRODUCT": (status.HTTP_400_BAD_REQUEST, "Response is not a Shopify product JSON"),
    "SHOPIFY_JSON_BLOCKED": (status.HTTP_403_FORBIDDEN, "Shopify JSON endpoint is blocked"),
    "PRODUCT_NOT_FOUND": (status.HTTP_404_NOT_FOUND, "Product not found"),

    # SCRAPER
    "SCRAPER_TIMEOUT": (status.HTTP_504_GATEWAY_TIMEOUT, "Shopify request timed out"),
    "SCRAPER_NETWORK_ERROR": (status.HTTP_502_BAD_GATEWAY, "Network error while fetching Shopify data"),
    "SCRAPER_FAILED": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Scraper failed"),

    # PROCESSING
    "PROCESSING_ERROR": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Product processing failed"),

    # STORAGE
    "STORAGE_FAILURE": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to store product data"),

    # SYSTEM
    "INTERNAL_SERVER_ERROR": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error"),
}
