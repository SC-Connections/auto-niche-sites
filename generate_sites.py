import os
import csv
import requests
from jinja2 import Template

# Environment variables from GitHub secrets
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "")

# Template paths
TEMPLATE_PATH = "site_template/index.html"
OUTPUT_DIR = "dist"
NICHES_CSV = "niches.csv"

# Ensure output folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_products(keyword):
    """Fetch product details from the RapidAPI Amazon API."""
    url = f"https://{RAPIDAPI_HOST}/product-search"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"query": keyword, "country": "US"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        products = data.get("data", {}).get("products", [])
        return products[:10]  # top 10 products
    except Exception as e:
        print(f"❌ API fetch failed for {keyword}: {e}")
        return []

def generate_page(niche, products):
    """Render and save an HTML page for a specific niche."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = Template(f.read())

    html = template.render(niche=niche, products=products, assoc_tag=ASSOC_TAG)

    niche_dir = os.path.join(OUTPUT_DIR, niche.replace(" ", "-").lower())
    os.makedirs(niche_dir, exist_ok=True)
    output_path = os.path.join(niche_dir, "index.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Page created: {output_path}")

def main():
    print("⚙️ Starting site generation...")

    with open(NICHES_CSV, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # skip header if present
        for row in reader:
            if not row:
                continue
            niche = row[0].strip()
            products = fetch_products(niche)
            generate_page(niche, products)

    print("🎉 All niche pages generated successfully.")

if __name__ == "__main__":
    main()
