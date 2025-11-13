import os
import csv
import requests
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# --- CONFIG ---
API_URL = "https://api.sc-connection-tools.com/products"
DIST_DIR = Path("dist")
TEMPLATE_DIR = Path("site_template")

# --- SETUP ---
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("index.html")

def fetch_products(niche):
    try:
        res = requests.get(API_URL, params={"q": niche}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, dict) and "data" in data:
            products = data["data"]
        elif isinstance(data, list):
            products = data
        else:
            print(f"⚠️ Unexpected 'data' format for {niche}: type={type(data)}")
            return []
        return products or []
    except Exception as e:
        print(f"❌ API fetch failed for {niche}: {e}")
        return []

def generate_page(niche):
    products = fetch_products(niche)
    output_dir = DIST_DIR / niche
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "index.html"
    html = template.render(title=niche.title(), products=products)
    output_file.write_text(html, encoding="utf-8")
    print(f"✅ Page created: {output_file}")

def main():
    DIST_DIR.mkdir(exist_ok=True)
    with open("niches.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        header = reader.fieldnames or []
        if "niche" not in header:
            print("⚠️ CSV missing 'niche' column — check file header.")
            return
        for row in reader:
            niche = row["niche"].strip().lower()
            if niche:
                generate_page(niche)
    print("🎉 All niche pages generated successfully.")

if __name__ == "__main__":
    print("⚙️ Starting site generation...")
    main()
