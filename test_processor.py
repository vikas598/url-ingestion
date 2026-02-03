import requests
import json

print("Testing data processing pipeline...")
print("Scraping and processing product...\n")

response = requests.post(
    'http://localhost:8000/api/v1/millex/scrape/product',
    json={'url': 'https://millex.in/products/millex-mother-root'}
)

result = response.json()

print('='*60)
print('API Response:')
print('='*60)
print(f'Status: {response.status_code}')
print(f'Result status: {result.get("status")}')
print(f'\nFile locations:')
print(f'  Raw file: {result.get("raw_file_path")}')
print(f'  Processed file: {result.get("processed_file_path")}')

if result.get('product'):
    prod = result['product']
    print(f'\nProcessed product data:')
    print(f'  Title: {prod.get("title")}')
    print(f'  Source: {prod.get("source")}')
    print(f'  Schema version: {prod.get("schema_version")}')
    print(f'  Currency: {prod.get("pricing", {}).get("currency")}')
    print(f'  Price: {prod.get("pricing", {}).get("price")}')
    
    # Check description cleaning
    desc_clean = prod.get('description', '')
    desc_html = prod.get('description_html', '')
    print(f'\nDescription cleaning:')
    print(f'  HTML length: {len(desc_html)} chars')
    print(f'  Clean text length: {len(desc_clean)} chars')
    print(f'  HTML removed: {len(desc_html) - len(desc_clean)} chars')
    
    if desc_clean:
        print(f'\n  First 150 chars of clean description:')
        print(f'    {desc_clean[:150]}...')
