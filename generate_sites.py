import os
import csv
import requests

# Environment variables from GitHub secrets
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "amazon24.p.rapidapi.com")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "")

# Template paths
TEMPLATE_PATH = "site_template/index.html"
OUTPUT_DIR = "dist"
NICHES_CSV = "niches.csv"

# Ensure dist folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_products(niche):
    """Fetch products from the Amazon API (via RapidAPI)."""
    url = f"https://{RAPIDAPI_HOST}/api/product"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    querystring = {"keyword": niche, "country": "US"}

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        # The API returns product results in different formats depending on endpoint
        items = data.get("result", []) or data.get("products", [])
        return items[:10]  # top 10
    except Exception as e:
        print(f"❌ API fetch failed for {niche}: {e}")
        return []


def build_product_cards(products):
    """Convert product list to HTML card grid."""
    cards = ""
    for p in products:
        title = p.get("title") or p.get("name") or "Unknown Product"
        image = p.get("image") or p.get("thumbnail") or ""
        link = p.get("url") or p.get("link") or "#"
        price = p.get("price") or p.get("current_price") or ""
        cards += f"""
        <div class="card">
            <img src="{image}" alt="{title}" loading="lazy"/>
            <h3>{title}</h3>
            <p>{price}</p>
            <a href="{link}?tag={ASSOC_TAG}" target="_blank">View on Amazon</a>
        </div>
        """
    return cards


def generate_site(niche):
    """Build one niche page and save it under /dist/niche/index.html."""
    products = fetch_products(niche)
    cards_html = build_product_cards(products)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    html = (
        template.replace("{{ niche }}", niche.title())
        .replace("{{ products }}", cards_html or "<p>No products found.</p>")
    )

    niche_dir = os.path.join(OUTPUT_DIR, niche.replace(" ", "-").lower())
    os.makedirs(niche_dir, exist_ok=True)

    output_path = os.path.join(niche_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Page created: {output_path}")


def main():
    """Generate static sites for all niches in the CSV."""
    if not RAPIDAPI_KEY:
        print("❌ Missing RAPIDAPI_KEY environment variable.")
        return

    if not os.path.exists(NICHES_CSV):
        print("❌ niches.csv not found.")
        return

    with open(NICHES_CSV, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:
                niche = row[0].strip()
                generate_site(niche)


if __name__ == "__main__":
    print("⚙️ Starting site generation...")
    main()
    print("🎉 All niche pages generated successfully.")
