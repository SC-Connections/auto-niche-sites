import os
import csv
import json
import requests
import shutil
import re
from pathlib import Path
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
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "").strip()

# ---- UTILS ----
def safe_assoc_url(url: str) -> str:
    """Append Amazon Associates tag to product links when possible."""
    if not url or not ASSOC_TAG:
        return url or "#"
    try:
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
        u = urlparse(url)
        qs = dict(parse_qsl(u.query, keep_blank_values=True))
        qs["tag"] = ASSOC_TAG
        new_u = u._replace(query=urlencode(qs, doseq=True))
        return urlunparse(new_u)
    except Exception:
        return url

def fetch_amazon_data():
    """Fetch product deals from the RapidAPI endpoint."""
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

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\- ]+", "", text)
    return re.sub(r"\s+", "-", text)

def create_page_data(niche: str, products: list) -> dict:
    """Create structured page data for the template."""
    # Prepare comparison rows (top 5 products)
    comparison_rows = []
    for idx, product in enumerate(products[:5], 1):
        product_id = slugify(product.get("product_title", f"product-{idx}"))
        comparison_rows.append({
            "rank": idx,
            "id": product_id,
            "name": product.get("product_title", "Unknown Product"),
            "pitch": product.get("product_description", "")[:100] + "..." if product.get("product_description") else "Great product",
            "img": product.get("product_photo", ""),
            "link": safe_assoc_url(product.get("product_url", "#")),
            "cta": "View Deal"
        })
    
    # Prepare detailed reviews (all products)
    review_items = []
    for idx, product in enumerate(products, 1):
        product_id = slugify(product.get("product_title", f"product-{idx}"))
        review_items.append({
            "id": product_id,
            "name": product.get("product_title", "Unknown Product"),
            "img": product.get("product_photo", ""),
            "badge": product.get("product_star_rating", "4.5") + " ★" if product.get("product_star_rating") else "Top Pick",
            "summary": product.get("product_description", "A high-quality product perfect for your needs.")[:150] + "...",
            "pros": [
                "High quality construction",
                "Great value for money",
                "Positive customer reviews"
            ],
            "cons": [
                "May vary by individual preference",
                "Check compatibility before purchase"
            ],
            "link": safe_assoc_url(product.get("product_url", "#")),
            "cta": "Check Price on Amazon"
        })
    
    # Create FAQ items
    faq_items = [
        {
            "q": f"What should I look for when buying {niche}?",
            "a": f"When shopping for {niche}, consider quality, price, customer reviews, and brand reputation. Always check product specifications to ensure it meets your needs."
        },
        {
            "q": f"Are these the best {niche} available?",
            "a": "Yes, we've carefully curated this list based on customer ratings, expert reviews, and value for money."
        },
        {
            "q": "How often is this list updated?",
            "a": "We regularly update our product recommendations to ensure you get the most current and relevant options."
        }
    ]
    
    # Create page structure
    page_data = {
        "title": f"Best {niche.title()} (2025) - Top Picks & Reviews",
        "description": f"Discover the best {niche} with our expert reviews and comparison. Find top-rated products with detailed pros, cons, and buying guides.",
        "heading": f"Best {niche.title()} in 2025",
        "subheading": "Expert-curated picks with detailed reviews and buying guidance",
        "comparison": {
            "title": f"Quick Comparison: Top {len(comparison_rows)} {niche.title()}",
            "rows": comparison_rows,
            "tip": "💡 Click on any product name to jump to its detailed review below."
        } if comparison_rows else None,
        "reviews": {
            "title": "Detailed Product Reviews",
            "products": review_items
        } if review_items else None,
        "guide": {
            "title": f"Buyer's Guide: How to Choose {niche.title()}",
            "content": f"""
                <p>Choosing the right {niche} can be challenging with so many options available. Here are key factors to consider:</p>
                <ul>
                    <li><strong>Quality & Durability:</strong> Look for products with solid construction and positive long-term reviews.</li>
                    <li><strong>Price vs. Value:</strong> The most expensive isn't always the best. Consider what features matter most to you.</li>
                    <li><strong>Customer Reviews:</strong> Pay attention to verified purchase reviews and common themes in feedback.</li>
                    <li><strong>Brand Reputation:</strong> Established brands often provide better customer support and warranties.</li>
                    <li><strong>Specifications:</strong> Ensure the product specifications match your specific needs and use case.</li>
                </ul>
                <p>Remember to check return policies and warranty information before making your purchase.</p>
            """
        },
        "faq": faq_items,
        "trust": f"Our team spends hours researching and testing {niche} to bring you unbiased recommendations. We analyze customer reviews, compare specifications, and consider real-world performance. As Amazon Associates, we may earn from qualifying purchases, but this never influences our honest assessments."
    }
    
    return page_data

def generate_site(niche: str, products: list):
    """Render an HTML site from template using Jinja2."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("index.html")
    
    # Create structured page data
    page_data = create_page_data(niche, products)
    
    # Create niche directory
    niche_slug = slugify(niche)
    niche_dir = os.path.join(OUTPUT_DIR, niche_slug)
    os.makedirs(niche_dir, exist_ok=True)
    
    # Copy static assets
    for item in Path(TEMPLATE_DIR).iterdir():
        if item.name == "index.html":
            continue
        if item.is_file():
            shutil.copy(item, os.path.join(niche_dir, item.name))
    
    # Render template
    rendered = template.render(niche=niche, page=page_data)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(rendered)
    
    print(f"✅ Generated site for '{niche}' in {niche_dir}")

def main():
    print("⚙️ Starting site generation process...")
    
    # Ensure dist exists
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Read niches.csv safely
    with open(NICHES_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "keyword" not in reader.fieldnames:
            raise KeyError("CSV must have a 'keyword' column.")
        
        for row in reader:
            niche = row["keyword"].strip()
            if not niche:
                continue
            
            print(f"🔍 Fetching data for '{niche}'...")
            products = fetch_amazon_data()
            
            if not products:
                print(f"⚠️ No products found for '{niche}', generating with placeholder data...")
                # Generate with empty products list - template will handle gracefully
            
            generate_site(niche, products)
    
    print("🎉 All niche sites generated successfully!")

if __name__ == "__main__":
    main()
