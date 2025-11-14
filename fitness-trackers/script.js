import csv
import os
import re
import requests
import shutil
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# === CONFIG ===
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # GitHub Secret
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "amazon24.p.rapidapi.com")  # adjust if needed
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "").strip()  # optional GitHub Secret, e.g., scconnec0d-20

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "site_template"
DIST_DIR = BASE_DIR / "dist"

# Example endpoint (adjust to your chosen RapidAPI Amazon API)
SEARCH_URL = f"https://{RAPIDAPI_HOST}/api/product"

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
        raise RuntimeError("Missing RAPIDAPI_KEY environment variable.")
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
        return normalized
    except Exception as e:
        print(f"⚠️ Error for niche '{niche}': {e}")
        return []

def render_cards(products):
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

def fill_template(niche_title: str, cards_html: str) -> str:
    with open(TEMPLATE_DIR / "index.html", "r", encoding="utf-8") as f:
        tpl = f.read()
    replacements = {
        "{{TITLE}}": f"Top {niche_title} (2025)",
        "{{DESCRIPTION}}": f"Best {niche_title.lower()} — curated picks with specs and links.",
        "{{H1}}": f"Best {niche_title} in 2025",
        "{{PRODUCT_CARDS}}": cards_html
    }
    for k, v in replacements.items():
        tpl = tpl.replace(k, v)
    return tpl

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\- ]+", "", text)
    return re.sub(r"\s+", "-", text)

def build_site(niche: str):
    niche_slug = slugify(niche)
    niche_dir = DIST_DIR / niche_slug
    niche_dir.mkdir(parents=True, exist_ok=True)

    # copy template assets
    for item in TEMPLATE_DIR.iterdir():
        if item.name == "index.html":
            continue
        if item.is_file():
            shutil.copy(item, niche_dir / item.name)

    products = fetch_products(niche)
    cards_html = render_cards(products)
    final_html = fill_template(niche.title(), cards_html)

    with open(niche_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

def main():
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    with open(BASE_DIR / "niches.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            niche = row.get("niche", "").strip()
            if niche:
                print(f"🛠️ Generating: {niche}")
                build_site(niche)

    print("✅ Generation complete. Built sites in /dist/<niche>/")

if __name__ == "__main__":
    main()
