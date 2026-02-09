from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, HttpUrl

from app.services.scrapers.millex.pipeline import run_collection_pipeline
from app.services.scrapers.millex.product import scrape_millex_product
from app.services.storage import store_product_data, store_products, store_collection
from app.services.storage import store_processed_product, store_processed_collection
from app.services.processor import process_millex_product
from app.services.embed_products import generate_product_embeddings
from app.services.search_service import load_resources

router = APIRouter(prefix="/millex", tags=["Millex"])


# URL validation helpers
def is_product_url(url: str) -> bool:
    """Check if URL is a product URL (contains /products/)"""
    return "/products/" in url


def is_collection_url(url: str) -> bool:
    """Check if URL is a collection URL (contains /collections/)"""
    return "/collections/" in url


class MillexCollectionRequest(BaseModel):
    url: HttpUrl


class MillexProductRequest(BaseModel):
    url: HttpUrl


class MillexHomepageRequest(BaseModel):
    url: HttpUrl


@router.post("/scrape/collection")
def scrape_collection(payload: MillexCollectionRequest, request: Request):
    """
    Scrape all products from a Millex collection page.
    All products are saved together in a single JSON file in data/products/ directory.
    Processed data is saved to data/processed/ directory.
    
    Example: {"url": "https://millex.in/collections/all"}
    """
    # Validate URL is a collection URL
    url_str = str(payload.url)
    if not is_collection_url(url_str):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL: This endpoint only accepts collection URLs (e.g., /collections/all). For product URLs, use the /scrape/product endpoint."
        )
    
    try:
        # Scrape all products from collection
        products = run_collection_pipeline(url_str)
        
        # Store raw collection data
        raw_file_path = store_collection(url_str, products)
        
        # Process all products
        processed_products = [process_millex_product(p) for p in products]
        
        # Store processed collection data
        processed_file_path = store_processed_collection(url_str, processed_products)
        
        # 🔄 Trigger embedding update
        try:
            print(f"Update embeddings for collection: {url_str}")
            count = generate_product_embeddings()
            load_resources(force=True)  # Reload search index
            embedding_status = f"Updated index with {count} products"
        except Exception as embed_err:
            print(f"Embedding update failed: {embed_err}")
            embedding_status = f"Failed to update index: {str(embed_err)}"
        
        return {
            "status": "success",
            "collection_url": url_str,
            "products_count": len(products),
            "raw_file_path": raw_file_path,
            "processed_file_path": processed_file_path,
            "embedding_status": embedding_status,
            "products": processed_products,  # Return processed data
            "request_id": request.state.request_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_id": request.state.request_id
        }


@router.post("/scrape/product")
def scrape_product(payload: MillexProductRequest, request: Request):
    """
    Scrape a single Millex product page.
    Product is automatically saved to data/products/ directory.
    Processed data is saved to data/processed/ directory.
    
    Example: {"url": "https://millex.in/products/millex-mother-root"}
    """
    # Validate URL is a product URL
    url_str = str(payload.url)
    if not is_product_url(url_str):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL: This endpoint only accepts product URLs (e.g., /products/product-name). For collection URLs, use the /scrape/collection endpoint."
        )
    
    try:
        # Scrape product
        product_data = scrape_millex_product(url_str)
        
        # Store raw product data
        raw_file_path = store_product_data(product_data)
        
        # Process the data (clean description, normalize fields)
        processed_data = process_millex_product(product_data)
        
        # Store processed data
        processed_file_path = store_processed_product(processed_data)
        
        # 🔄 Trigger embedding update
        try:
            print(f"Update embeddings for product: {url_str}")
            count = generate_product_embeddings()
            load_resources(force=True)  # Reload search index
            embedding_status = f"Updated index with {count} products"
        except Exception as embed_err:
            print(f"Embedding update failed: {embed_err}")
            embedding_status = f"Failed to update index: {str(embed_err)}"
        
        return {
            "status": "success",
            "raw_file_path": raw_file_path,
            "processed_file_path": processed_file_path,
            "embedding_status": embedding_status,
            "product": processed_data,  # Return processed data
            "request_id": request.state.request_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_id": request.state.request_id
        }


@router.get("/health")
def health():
    """
    Health check endpoint for Millex scraper.
    """
    return {
        "status": "ok",
        "scraper": "millex",
        "version": "1.0"
    }


@router.post("/scrape/homepage")
def scrape_homepage_endpoint(payload: MillexHomepageRequest, request: Request):
    """
    Scrape all products from Millex homepage.
    Extracts product URLs from homepage and scrapes full product data for each.
    All products are saved together in a single JSON file.
    Processed data is saved to data/processed/ directory.
    
    Example: {"url": "https://millex.in"}
    """
    try:
        # Import the updated function
        from app.services.scrapers.millex.homepage import scrape_homepage_products
        
        # Scrape all products from homepage
        products = scrape_homepage_products(str(payload.url))
        
        # Store raw homepage data
        raw_file_path = store_collection(str(payload.url), products)
        
        # Process all products
        processed_products = [process_millex_product(p) for p in products]
        
        # Store processed homepage data
        processed_file_path = store_processed_collection(str(payload.url), processed_products)
        
        # 🔄 Trigger embedding update
        try:
            print(f"Update embeddings for homepage: {str(payload.url)}")
            count = generate_product_embeddings()
            load_resources(force=True)  # Reload search index
            embedding_status = f"Updated index with {count} products"
        except Exception as embed_err:
            print(f"Embedding update failed: {embed_err}")
            embedding_status = f"Failed to update index: {str(embed_err)}"
        
        return {
            "status": "success",
            "homepage_url": str(payload.url),
            "products_count": len(products),
            "raw_file_path": raw_file_path,
            "processed_file_path": processed_file_path,
            "embedding_status": embedding_status,
            "products": processed_products,  # Return processed data
            "request_id": request.state.request_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "request_id": request.state.request_id
        }
