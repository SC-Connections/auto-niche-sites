import csv
import os
import json
import requests
from jinja2 import Environment, FileSystemLoader

# -------------------------------
# Environment variables (from GitHub Secrets)
# -------------------------------
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
AMAZON_ASSOC_TAG = os.getenv("AMAZON_ASSOC_TAG", "scconnections-20")

# -------------------------------
# API fetch function
# -------------------------------
def fetch_amazon_data(keyword):
    """Fetch product data from Amazon Real Time API (via RapidAPI)."""
    url = "https://amazon-real-time-api.p.rapidapi.com/dealsByCategory"

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    params = {"category": keyword, "country": "US"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # ✅ Handle the RapidAPI response format
        if isinstance(data, dict):
            if "deals" in data and isinstance(data["deals"], list):
                return data["deals"]
            elif "products" in data and isinstance(data["products"], list):
                return data["products"]
            else:
                print(f"⚠️ Unexpected 'data' format for {keyword}: type={type(data)} keys={list(data.keys())}")
                return []
        elif isinstance(data, list):
            return data
        else:
            print(f"⚠️ Unknown data type for {keyword}: {type(data)}")
            return []

    except Exception as e:
        print(f"❌ Error fetching data for {keyword}: {e}")
        return []

# -------------------------------
# HTML generation function
# -------------------------------
def generate_page(env, keyword, products):
    """Render HTML page for a niche keyword."""
    template = env.get_template("index.html")

    # Define the output directory for each niche
    output_dir = os.path.join("dist", keyword)
    os.makedirs(output_dir, exist_ok=True)

    # Render template
    html_content = template.render(
        keyword=keyword,
        products=products,
        amazon_tag=AMAZON_ASSOC_TAG,
    )

    # Save the file
    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Page created: {output_path}")

# -------------------------------
# Main build logic
# -------------------------------
def main():
    print("⚙️ Starting site generation...")

    # Initialize Jinja2 environment
    env = Environment(loader=FileSystemLoader("site_template"))

    # Ensure niches.csv exists
    if not os.path.exists("niches.csv"):
        print("❌ niches.csv not found.")
        return

    with open("niches.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames or []

        # Check for proper column
        if "keyword" not in headers and "niche" not in headers:
            print("⚠️ CSV missing 'keyword' or 'niche' column — check file header.")
            return

        for row in reader:
            keyword = (row.get("keyword") or row.get("niche") or "").strip()
            if not keyword:
                continue

            print(f"🔍 Fetching data for '{keyword}'...")
            products = fetch_amazon_data(keyword)

            if not products:
                print(f"⚠️ No products found for '{keyword}'. Skipping.")
                continue

            generate_page(env, keyword, products)

    print("🎉 All niche pages generated successfully.")

# -------------------------------
# Run script
# -------------------------------
if __name__ == "__main__":
    main()
