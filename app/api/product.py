from fastapi import APIRouter, Request
from app.models.request import ProductIngestRequest
from app.services.url_handler import build_shopify_json_url
from app.services.scraper import fetch_shopify_product
from app.services.processor import process_shopify_product

router = APIRouter()

@router.post("/product")
def ingest_product(payload: ProductIngestRequest, request: Request):
    json_url = build_shopify_json_url(str(payload.url))
    raw_data = fetch_shopify_product(json_url)

    processed = process_shopify_product(
        raw_data=raw_data,
        source_url=str(payload.url)
    )

    return {
        "status": "success",
        "product_id": processed["product_id"],
        "data": processed,
        "request_id": request.state.request_id
    }
