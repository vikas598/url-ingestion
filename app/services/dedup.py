"""
Deduplication utilities for scraping workflow.
Tracks which products have already been scraped to avoid wasting time.
"""

import os
import json
from pathlib import Path
from typing import Optional, Set

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "products")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def extract_product_id_from_url(url: str) -> str:
    """
    Extract product ID from URL.
    Example: https://millex.in/products/product-name -> product-name
    """
    # Remove query parameters
    if '?' in url:
        url = url.split('?')[0]
    
    # Extract last path segment
    parts = url.rstrip('/').split('/')
    if len(parts) > 0:
        return parts[-1]
    
    return ""


def get_scraped_product_ids() -> Set[str]:
    """
    Get set of all product IDs that have already been scraped.
    Checks both raw and processed directories.
    """
    scraped_ids = set()
    
    # Check raw products directory
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json') and not any(x in filename for x in ['homepage', 'collection', 'all']):
                # Extract ID from filename (remove .json extension)
                product_id = filename.replace('.json', '')
                scraped_ids.add(product_id)
    
    # Check processed products directory
    if os.path.exists(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
            if filename.endswith('.json') and not any(x in filename for x in ['homepage', 'processed', 'all']):
                product_id = filename.replace('.json', '')
                scraped_ids.add(product_id)
    
    return scraped_ids


def is_product_already_scraped(url: str) -> bool:
    """
    Check if a product URL has already been scraped.
    
    Args:
        url: Product URL to check
        
    Returns:
        True if product is already scraped, False otherwise
    """
    product_id = extract_product_id_from_url(url)
    if not product_id:
        return False
    
    scraped_ids = get_scraped_product_ids()
    return product_id in scraped_ids


def get_product_file_path(url: str) -> Optional[str]:
    """
    Get the file path of an already-scraped product.
    Returns None if product hasn't been scraped yet.
    
    Args:
        url: Product URL
        
    Returns:
        File path if exists, None otherwise
    """
    product_id = extract_product_id_from_url(url)
    if not product_id:
        return None
    
    # Check processed directory first (preferred)
    processed_path = os.path.join(PROCESSED_DIR, f"{product_id}.json")
    if os.path.exists(processed_path):
        return processed_path
    
    # Fall back to raw directory
    raw_path = os.path.join(DATA_DIR, f"{product_id}.json")
    if os.path.exists(raw_path):
        return raw_path
    
    return None


def filter_unscraped_urls(urls: list[str]) -> list[str]:
    """
    Filter a list of URLs to only include those not yet scraped.
    
    Args:
        urls: List of product URLs
        
    Returns:
        List of URLs that haven't been scraped yet
    """
    scraped_ids = get_scraped_product_ids()
    unscraped = []
    
    for url in urls:
        product_id = extract_product_id_from_url(url)
        if product_id and product_id not in scraped_ids:
            unscraped.append(url)
    
    return unscraped
