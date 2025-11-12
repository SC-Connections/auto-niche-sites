import os
import csv
import requests
import subprocess
from jinja2 import Template

# --- Configuration ---
API_URL = "https://amazon-real-time-api.p.rapidapi.com/search"
API_KEY = os.getenv("RAPIDAPI_KEY")  # Stored in GitHub Secrets
HEADERS = {
    "x-rapidapi-host": "amazon-real-time-api.p.rapidapi.com",
    "x-rapidapi-key": API_KEY or "MISSING_KEY"
}
OUTPUT_DIR = "dist"
TEMPLATE_PATH = "site_template/index.html"

# --- Load Jinja2 template ---
def load_template():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return Template(f.read())

# --- Fetch products from API ---
def fetch_products(keyword, country="US", max_items=10):
    params = {
        "query": keyword,
        "domain": country,
        "sort": "relevance",
        "page": 1,
        "pages": 1
    }

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=20)
        response.raise_for_status()
        result = response.json()

        # ✅ Handle new wrapped API structure
        if isinstance(result, dict):
            if "data" in result:
                data = result["data"]
                if isinstance(data, dict) and "products" in data:
                    products = data["products"]
                elif isinstance(data, list):
                    products = data
                else:
                    print(f"⚠️ Unexpected 'data' format for {keyword}: type={type(data)}")
                    products = []
            elif "success" in result and "metadata" in result:
                # Some APIs wrap results differently — log keys to debug
                print(f"⚠️ Unexpected response for {keyword}: {list(result.keys())}")
                products = []
            else:
                print(f"⚠️ No 'data' key found in response for {keyword}")
                products = []
        else:
            print(f"⚠️ Non-dict API response for {keyword}")
            products = []

        # Trim items if available
        return products[:max_items] if products else []

    except Exception as e:
        print(f"❌ API fetch failed for {keyword}: {e}")
        return []

# --- Generate static site for each niche ---
def generate_site(keyword, products):
    os.makedirs(f"{OUTPUT_DIR}/{keyword}", exist_ok=True)
    template = load_template()

    html = template.render(
        title=f"{keyword.capitalize()} - Amazon Niche Products",
        keyword=keyword,
        products=products
    )

    with open(f"{OUTPUT_DIR}/{keyword}/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Page created: {OUTPUT_DIR}/{keyword}/index.html")

# --- Main build function ---
def main():
    print("⚙️ Starting site generation...")

    with open("niches.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            keyword = row["keyword"].strip()
            if not keyword:
                continue
            products = fetch_products(keyword)
            generate_site(keyword, products)

    print("🎉 All niche pages generated successfully.")

    # Deploy to gh-pages
    try:
        subprocess.run(["git", "add", OUTPUT_DIR], check=True)
        subprocess.run(["git", "commit", "-m", "Update generated niche pages"], check=False)
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        print("🚀 Deployment complete.")
    except Exception as e:
        print(f"⚠️ Deployment skipped: {e}")

if __name__ == "__main__":
    main()
