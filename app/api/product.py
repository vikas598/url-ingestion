from fastapi import APIRouter, Request
from app.models.request import ProductIngestRequest
from app.services.url_handler import build_shopify_json_url
from app.services.scraper import fetch_shopify_product

router = APIRouter()

@router.post("/product")
def ingest_product(payload: ProductIngestRequest, request: Request):
    json_url = build_shopify_json_url(str(payload.url))
    raw_data = fetch_shopify_product(json_url)

    return {
        "status": "success",
        "product_id": None,
        "data": raw_data,
        "request_id": request.state.request_id
    }
