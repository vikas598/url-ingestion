from fastapi import APIRouter
from pydantic import BaseModel
from app.services.recommender_system.search_service import search_products

router = APIRouter()

class SearchRequest(BaseModel):
    query: str

@router.post("/search")
async def search(search_req: SearchRequest):
    results = search_products(search_req.query)
    return {"results": results}
