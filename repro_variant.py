import sys
import os
import requests
from bs4 import BeautifulSoup
import json

# Ensure app can be imported
sys.path.append(os.getcwd())

try:
    from app.services.scrapers.millex.product import scrape_millex_product
    
    url = "https://millex.in/products/millex-millet-health-mix-without-chrunam?variant=45297908875420"
    print(f"Fetching {url}...")
    
    data = scrape_millex_product(url)
    variants = data.get("variants", [])
    print(f"Result: {len(variants)} variants found.")
    print(json.dumps(variants, indent=2))
    
except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Runtime Error: {e}")
