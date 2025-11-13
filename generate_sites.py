import os
import csv
import re
import requests
import shutil
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# ---- CONFIG ----
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "amazon24.p.rapidapi.com")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "").strip()

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "site_template"
OUTPUT_DIR = BASE_DIR / "dist"
NICHES_FILE = BASE_DIR / "niches.csv"

# RapidAPI endpoint for product search
SEARCH_URL = f"https://{RAPIDAPI_HOST}/api/product"

# ---- UTILS ----
def safe_assoc_url(url: str) -> str:
    """Append Amazon Associates tag to product links when possible."""
    if not url or not ASSOC_TAG:
        return url or "#"
    try:
        u = urlparse(url)
        qs = dict(parse_qsl(u.query, keep_blank_values=True))
        qs["tag"] = ASSOC_TAG
        new_u = u._replace(query=urlencode(qs, doseq=True))
        return urlunparse(new_u)
    except Exception:
        return url

def fetch_products(niche: str):
    """Fetch up to 10 products for the niche using RapidAPI."""
    if not RAPIDAPI_KEY:
        print("⚠️ Missing RAPIDAPI_KEY environment variable. Using mock data.")
        return create_mock_products(niche)
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {"keyword": niche, "country": "US", "page": "1"}
    
    try:
        r = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        items = data.get("docs") or data.get("data") or data.get("results") or []
        products = items[:10]
        
        normalized = []
        for p in products:
            title = p.get("product_title") or p.get("title") or "Unknown Product"
            img = p.get("product_main_image_url") or p.get("image") or ""
            price = (
                p.get("product_price") or
                p.get("price") or
                p.get("app_sale_price") or
                "N/A"
            )
            url = p.get("product_detail_url") or p.get("url") or "#"
            url = safe_assoc_url(url)
            rating = (p.get("product_star_rating") or p.get("rating") or "")
            reviews = (p.get("product_num_ratings") or p.get("reviews_count") or "")
            
            normalized.append({
                "title": title,
                "image": img,
                "price": price,
                "url": url,
                "rating": rating,
                "reviews": reviews
            })
        
        return normalized if normalized else create_mock_products(niche)
    except Exception as e:
        print(f"⚠️ Error fetching data for '{niche}': {e}")
        return create_mock_products(niche)

def create_mock_products(niche: str):
    """Create mock products for testing/demo purposes."""
    return [
        {
            "title": f"Premium {niche.title()} - Best Seller",
            "image": "https://via.placeholder.com/300x300?text=Product+1",
            "price": "$99.99",
            "url": "#",
            "rating": "4.5",
            "reviews": "1,234"
        },
        {
            "title": f"Professional {niche.title()} Kit",
            "image": "https://via.placeholder.com/300x300?text=Product+2",
            "price": "$149.99",
            "url": "#",
            "rating": "4.7",
            "reviews": "856"
        },
        {
            "title": f"Budget {niche.title()} Option",
            "image": "https://via.placeholder.com/300x300?text=Product+3",
            "price": "$49.99",
            "url": "#",
            "rating": "4.2",
            "reviews": "423"
        }
    ]

def render_cards(products):
    """Render product cards as HTML."""
    cards = []
    for p in products:
        rating_bits = []
        if p["rating"]:
            rating_bits.append(f"<span class='badge'>⭐ {p['rating']}</span>")
        if p["reviews"]:
            rating_bits.append(f"<span class='badge'>{p['reviews']} reviews</span>")
        rating_html = " ".join(rating_bits)
        
        cards.append(f"""
        <article class="card">
          <img src="{p['image']}" alt="{p['title']}" loading="lazy" />
          <h3>{p['title']}</h3>
          <div class="price">{p['price']}</div>
          <div>{rating_html}</div>
          <a class="btn" href="{p['url']}" target="_blank" rel="nofollow sponsored noopener">View on Amazon</a>
        </article>
        """)
    
    return "\n".join(cards) if cards else "<p>No products found right now.</p>"

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\- ]+", "", text)
    return re.sub(r"\s+", "-", text)

def generate_site(niche: str):
    """Generate a complete site for a niche."""
    niche_slug = slugify(niche)
    niche_dir = OUTPUT_DIR / niche_slug
    niche_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy CSS and other static assets
    for item in TEMPLATE_DIR.iterdir():
        if item.name == "index.html":
            continue
        if item.is_file() and item.suffix in [".css", ".js", ".png", ".jpg", ".ico"]:
            shutil.copy(item, niche_dir / item.name)
    
    # Fetch products
    print(f"🔍 Fetching products for '{niche}'...")
    products = fetch_products(niche)
    
    # Render HTML
    cards_html = render_cards(products)
    
    # Read and process template
    with open(TEMPLATE_DIR / "index.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # Replace template variables
    html = html.replace("{{ niche }}", niche.title())
    html = html.replace("{{ products }}", cards_html)
    
    # Write final HTML
    with open(niche_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Generated site for '{niche}' at {niche_dir}")

def main():
    print("⚙️ Starting site generation process...")
    
    # Clean and create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read niches from CSV
    with open(NICHES_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Support both 'keyword' and 'niche' column names
        if "keyword" in reader.fieldnames:
            niche_column = "keyword"
        elif "niche" in reader.fieldnames:
            niche_column = "niche"
        else:
            raise KeyError("CSV must have either a 'keyword' or 'niche' column.")
        
        for row in reader:
            niche = row[niche_column].strip()
            if niche:
                generate_site(niche)
    
    print(f"🎉 All sites generated! Check the {OUTPUT_DIR} directory.")

if __name__ == "__main__":
    main()
