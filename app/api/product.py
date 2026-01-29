from fastapi import APIRouter, Request
from app.models.request import ProductIngestRequest

router = APIRouter()

@router.post("/product")
def ingest_product(payload: ProductIngestRequest, request: Request):
    # pipeline will be wired next
    return {
        "status": "success",
        "message": "Pipeline not wired yet"
    }
