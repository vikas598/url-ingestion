import requests
import json

print("Testing enhanced homepage scraper...")
print("This will scrape all products from the homepage\n")

response = requests.post(
    'http://localhost:8000/api/v1/millex/scrape/homepage',
    json={'url': 'https://millex.in'}
)

result = response.json()
print('Status:', response.status_code)
print('Result status:', result.get('status'))
print('Products scraped:', result.get('products_count'))
print('File path:', result.get('file_path'))

if result.get('products'):
    print(f'\nFirst product scraped:')
    first_product = result['products'][0]
    print(f'  Title: {first_product.get("title")}')
    print(f'  URL: {first_product.get("url")}')
    print(f'  Price: {first_product.get("price", "N/A")}')
    print(f'  Currency: {first_product.get("currency", "N/A")}')
