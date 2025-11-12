import os
import csv
import requests

# --- CONFIGURATION ---
OUTPUT_DIR = "dist"
TEMPLATE_DIR = "site_template"
NICHES_FILE = "niches.csv"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "amazon24.p.rapidapi.com")
ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "")

# --- HELPERS ---
def fetch_amazon_products(keyword):
    """Fetch product data from Amazon via RapidAPI"""
    url = f"https://{RAPIDAPI_HOST}/api/product"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    querystring = {"keyword": keyword, "country": "US", "categoryID": "aps"}
    try:
        r = requests.get(url, headers=headers, params=querystring, timeout=20)
        data = r.json()
        return data.get("data", [])[:10]  # return top 10 results
    except Exception as e:
        print(f"❌ API fetch failed for {keyword}: {e}")
        return []

def create_site(niche, products):
    """Generate HTML file for a niche using the template"""
    niche_dir = os.path.join(OUTPUT_DIR, niche.replace(" ", "-").lower())
    os.makedirs(niche_dir, exist_ok=True)

    # Load template index.html
    template_path = os.path.join(TEMPLATE_DIR, "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Build product HTML blocks
    product_html = ""
    for p in products:
        title = p.get("product_title", "Unknown Product")
        image = p.get("product_photo", "")
        link = p.get("product_url", "#")
        if ASSOC_TAG and "amazon.com" in link:
            link += f"?tag={ASSOC_TAG}"
        price = p.get("app_sale_price", "N/A")

        product_html += f"""
        <div class='product'>
            <img src='{image}' alt='{title}' loading='lazy'>
            <h3>{title}</h3>
            <p>${price}</p>
            <a href='{link}' target='_blank'>Buy on Amazon</a>
        </div>
        """

    html_output = template.replace("{{ niche }}", niche).replace("{{ products }}", product_html)

    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"✅ Generated site for: {niche}")

# --- MAIN EXECUTION ---
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(NICHES_FILE, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not row: 
                continue
            niche = row[0].strip()
            products = fetch_amazon_products(niche)
            create_site(niche, products)

if __name__ == "__main__":
    main()
