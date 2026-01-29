from fastapi import APIRouter, Request
from app.models.request import ProductIngestRequest
from app.services.url_handler import build_shopify_json_url

router = APIRouter()

@router.post("/product")
def ingest_product(payload: ProductIngestRequest, request: Request):
    json_url = build_shopify_json_url(str(payload.url))

    return {
        "status": "success",
        "product_id": None,
        "data": {
            "json_url": json_url
        },
        "request_id": request.state.request_id
    }
