import os
import csv
import json
import requests
import shutil
from jinja2 import Environment, FileSystemLoader

# ---- CONFIG ----
RAPIDAPI_URL = "https://amazon-real-time-api.p.rapidapi.com/deals"
RAPIDAPI_HEADERS = {
    "x-rapidapi-host": "amazon-real-time-api.p.rapidapi.com",
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY")
}
RAPIDAPI_PARAMS = {"domain": "US", "node_id": "16310101"}

TEMPLATE_DIR = "site_template"
OUTPUT_DIR = "dist"
NICHES_FILE = "niches.csv"

# ---- UTILS ----
def fetch_amazon_data():
    """Fetch product deals from the new RapidAPI endpoint."""
    try:
        response = requests.get(RAPIDAPI_URL, headers=RAPIDAPI_HEADERS, params=RAPIDAPI_PARAMS)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"⚠️ API returned {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

def get_placeholder_products():
    """Generate placeholder product data."""
    return [
        {
            "title": "Product 1",
            "price": "$29.99",
            "rating": 4.5,
            "image": "https://via.placeholder.com/300x300?text=Product+1",
            "url": "https://amazon.com"
        },
        {
            "title": "Product 2",
            "price": "$39.99",
            "rating": 4.3,
            "image": "https://via.placeholder.com/300x300?text=Product+2",
            "url": "https://amazon.com"
        },
        {
            "title": "Product 3",
            "price": "$49.99",
            "rating": 4.7,
            "image": "https://via.placeholder.com/300x300?text=Product+3",
            "url": "https://amazon.com"
        }
    ]

def generate_site(niche, products):
    """Render an HTML site from template."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("index.html")

    niche_dir = os.path.join(OUTPUT_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)

    rendered = template.render(niche=niche, products=products)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(rendered)
    
    # Copy static files
    for static_file in ["style.css", "script.js"]:
        src = os.path.join(TEMPLATE_DIR, static_file)
        dst = os.path.join(niche_dir, static_file)
        if os.path.exists(src):
            shutil.copy2(src, dst)

def main():
    print("⚙️ Starting site generation process...")

    # Ensure dist exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read niches.csv safely
    with open(NICHES_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "keyword" not in reader.fieldnames:
            raise KeyError("CSV must have a 'keyword' column.")
        for row in reader:
            niche = row["keyword"].strip()
            print(f"🔍 Fetching data for '{niche}'...")
            products = fetch_amazon_data()
            
            if not products:
                print(f"⚠️ No products found for '{niche}', generating with placeholder data...")
                products = get_placeholder_products()
            
            generate_site(niche, products)
            print(f"✅ Generated site for '{niche}' in {OUTPUT_DIR}/{niche}")

    print("🎉 All niche sites generated successfully!")

if __name__ == "__main__":
    main()
