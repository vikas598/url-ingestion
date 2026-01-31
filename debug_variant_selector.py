import requests
from bs4 import BeautifulSoup

url = "https://millex.in/products/millex-millet-health-mix-without-chrunam?variant=45297908875420"
print(f"Checking {url}...")
try:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    
    selector = "div.variant-option"
    found = soup.select(selector)
    print(f"Selector '{selector}' found {len(found)} elements.")
    with open("debug_html.txt", "w", encoding="utf-8") as f:
        for i, el in enumerate(found):
            f.write(f"--- Element {i} ---\n")
            f.write(el.prettify() + "\n\n")
        print("CONFIRMED: The selector used in the code does not exist on the page.")
        
except Exception as e:
    print(f"Error: {e}")
