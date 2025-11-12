import os
import csv
import requests
from jinja2 import Template

# Environment variables from GitHub secrets
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "amazon-real-time-api.p.rapidapi.com")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "")

# Template paths
TEMPLATE_PATH = "site_template/index.html"
OUTPUT_DIR = "dist"
NICHES_CSV = "niches.csv"

# Ensure output folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_products(keyword):
    """Fetch product details from the Amazon Real Time API."""
    url = f"https://{RAPIDAPI_HOST}/search"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {
        "query": keyword,
        "domain": "US",
        "sort": "relevance",
        "page": 1,
        "pages": 1
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Check structure of response
        if "data" in data and isinstance(data["data"], list):
            products = data["data"]
        elif "data" in data and isinstance(data["data"], dict) and "products" in data["data"]:
            products = data["data"]["products"]
        else:
            print(f"⚠️ Unexpected response for {keyword}: {list(data.keys())}")
            return []

        # Limit to top 10 results
        return products[:10]

    except requests.exceptions.HTTPError as e:
        print(f"❌ API fetch failed for {keyword}: {e}")
    except Exception as e:
        print(f"❌ Error for {keyword}: {e}")
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
