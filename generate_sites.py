import os
import csv
import requests
from pathlib import Path
from jinja2 import Template

# Environment variables (from GitHub secrets)
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "")

# Template and paths
TEMPLATE_PATH = "site_template/index.html"
OUTPUT_DIR = Path("dist")
NICHES_CSV = "niches.csv"

OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_products(niche):
    """Fetch top products from RapidAPI (real-time-amazon-data)."""
    url = f"https://{RAPIDAPI_HOST}/search"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    params = {"query": niche, "page": "1", "country": "US"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("data", {}).get("products", [])
        return items[:10]
    except Exception as e:
        print(f"❌ API fetch failed for {niche}: {e}")
        return []

def make_product_cards(products):
    """Convert product data into HTML cards."""
    cards = []
    for p in products:
        title = p.get("title", "No title")
        image = p.get("main_image", "")
        price = p.get("price_str", "N/A")
        url = p.get("product_url", "#")

        card = f"""
        <article class="card">
            <img src="{image}" alt="{title}">
            <h2>{title}</h2>
            <p class="price">{price}</p>
            <a href="{url}?tag={ASSOC_TAG}" target="_blank">View on Amazon</a>
        </article>
        """
        cards.append(card)
    return "\n".join(cards)

def generate_site(niche, title, description):
    """Generate HTML page for one niche."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template_html = f.read()

    products = fetch_products(niche)
    cards_html = make_product_cards(products)

    html = (
        template_html.replace("{{TITLE}}", title)
        .replace("{{DESCRIPTION}}", description)
        .replace("{{H1}}", title)
        .replace("{{PRODUCT_CARDS}}", cards_html or "<p>No products found.</p>")
    )

    output_path = OUTPUT_DIR / niche / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"✅ Page created: {output_path}")

def main():
    print("⚙️ Starting site generation...")
    with open(NICHES_CSV, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            niche = row["niche"]
            title = row.get("title", niche.title())
            description = row.get("description", f"Top {title} available on Amazon.")
            generate_site(niche, title, description)
    print("🎉 All niche pages generated successfully.")

if __name__ == "__main__":
    main()
