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
GITHUB_USER = "SC-Connections"
TOKEN = os.getenv("GITHUB_TOKEN")

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

def generate_site(niche, products):
    """Render an HTML site from template."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("index.html")

    niche_dir = os.path.join(OUTPUT_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)

    rendered = template.render(niche=niche, products=products)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(rendered)


def copy_static_assets(niche):
    """Copy static CSS and JS files to the niche directory."""
    niche_dir = os.path.join(OUTPUT_DIR, niche)
    
    # Copy style.css
    src_css = os.path.join(TEMPLATE_DIR, "style.css")
    if os.path.exists(src_css):
        shutil.copy(src_css, os.path.join(niche_dir, "style.css"))
    
    # Copy script.js
    src_js = os.path.join(TEMPLATE_DIR, "script.js")
    if os.path.exists(src_js):
        shutil.copy(src_js, os.path.join(niche_dir, "script.js"))
    
    print(f"✅ Generated site for {niche}")

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
            generate_site(niche, products)
            copy_static_assets(niche)

    print("🎉 All niche sites generated and deployed!")

if __name__ == "__main__":
    main()
