from fastapi import FastAPI
from app.api.product import router as product_router

app = FastAPI(
    title="URL Ingestor",
    version="1.0"
)

app.include_router(product_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
