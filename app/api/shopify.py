from fastapi import APIRouter, Request
from app.services.scrapers.shopify.orchestrator import scrape_shopify_store

router = APIRouter(prefix="/shopify", tags=["Shopify"])


@router.post("/store")
def ingest_shopify_store(request: Request, payload: dict):
    store_url = payload.get("url")
    limit_collections = payload.get("limit_collections", 1)

    if not store_url:
        return {"error": "url is required"}

    data = scrape_shopify_store(
        store_url=store_url,
        limit_collections=limit_collections
    )

    return {
        "status": "success",
        "store": store_url,
        "collections_scraped": data["collections_scraped"],
        "products_scraped": data["products_scraped"],
        "request_id": request.state.request_id,
    }
