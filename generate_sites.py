import os
import csv
import requests
from jinja2 import Environment, FileSystemLoader

# Constants
BASE_URL = "https://amazon-real-time-api.p.rapidapi.com/deals"
HEADERS = {
    "x-rapidapi-host": "amazon-real-time-api.p.rapidapi.com",
    "x-rapidapi-key": os.getenv("RAPIDAPI_KEY", "")
}

DIST_DIR = "dist"
TEMPLATE_DIR = "site_template"

# Initialize template environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("index.html")

def fetch_amazon_data(niche, node_id="16310101"):
    """Fetch product data from RapidAPI endpoint."""
    url = f"{BASE_URL}?domain=US&node_id={node_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not data or "data" not in data:
            print(f"⚠️ No valid data returned for {niche}")
            return []
        return data["data"][:10]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {niche}: {e}")
        return []

def generate_site(niche, products):
    """Generate static HTML for each niche."""
    niche_dir = os.path.join(DIST_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)
    html_output = template.render(
        niche=niche.replace("-", " ").title(),
        products=products
    )
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"✅ Generated site for '{niche}' → {niche_dir}")

def main():
    print("⚙️ Starting site generation process...")
    os.makedirs(DIST_DIR, exist_ok=True)

    with open("niches.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            niche = row["keyword"].strip()
            print(f"🔍 Fetching deals for '{niche}'...")
            products = fetch_amazon_data(niche)
            generate_site(niche, products)

    print("🎉 All niche sites generated successfully!")

if __name__ == "__main__":
    main()
