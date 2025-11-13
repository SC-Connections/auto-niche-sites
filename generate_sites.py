import os
import csv
import requests
from jinja2 import Environment, FileSystemLoader

# === CONFIGURATION ===
OUTPUT_DIR = "dist"
TEMPLATE_DIR = "site_template"
HTML_TEMPLATE = "index.html"

# RapidAPI setup
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG")

if not RAPIDAPI_KEY or not RAPIDAPI_HOST or not ASSOC_TAG:
    raise EnvironmentError("Missing required environment variables: RAPIDAPI_KEY, RAPIDAPI_HOST, AMAZON_ASSOC_TAG")

# === HELPERS ===

def fetch_products(keyword):
    """Fetch product data from RapidAPI for a given keyword."""
    url = f"https://{RAPIDAPI_HOST}/searchProducts"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {
        "query": keyword,
        "country": "US",
        "page": 1
    }

    try:
        print(f"🔍 Fetching data for '{keyword}'...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Normalize results depending on API shape
        items = data.get("data") or data.get("products") or []
        if not items:
            print(f"⚠️ No products found for '{keyword}'.")
            return []

        products = []
        for item in items[:10]:  # limit to top 10 for simplicity
            products.append({
                "title": item.get("title", "Unknown Product"),
                "url": item.get("url", "#"),
                "price": item.get("price", "N/A"),
                "image": item.get("image", ""),
            })
        return products

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {keyword}: {e}")
        return []


def generate_site(niche, products):
    """Render and save an HTML page for a niche."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(HTML_TEMPLATE)
    output_html = template.render(
        niche=niche.title().replace("-", " "),
        products=products,
        amazon_tag=ASSOC_TAG
    )

    niche_dir = os.path.join(OUTPUT_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(output_html)
    print(f"✅ Page created: {niche_dir}/index.html")


def read_niches(csv_file="niches.csv"):
    """Read niche list from CSV."""
    niches = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "keyword" not in reader.fieldnames:
            raise ValueError("CSV file must contain a 'keyword' column.")
        for row in reader:
            niche = row["keyword"].strip().lower()
            if niche:
                niches.append(niche)
    return niches


# === MAIN ===
if __name__ == "__main__":
    print("⚙️ Starting site generation...")

    niches = read_niches()
    for niche in niches:
        products = fetch_products(niche)
        generate_site(niche, products)

    print("🎉 All niche pages generated successfully.")
