import os, csv, requests, json, time, re, subprocess

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "real-time-amazon-data.p.rapidapi.com"
GITHUB_TOKEN = os.getenv("GH_TOKEN")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST
}

API_BASE = f"https://{RAPIDAPI_HOST}"

def clean_slug(name):
    return re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-')

def safe_request(url, params):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
            r.raise_for_status()
            time.sleep(0.25)  # stay under 5 requests/sec
            return r.json().get("data", [])
        except requests.exceptions.HTTPError as e:
            if r.status_code == 429:
                print("Rate limit hit. Waiting 3s...")
                time.sleep(3)
            elif r.status_code == 403:
                print("403 Forbidden: Check RapidAPI key or subscription.")
                raise
            else:
                print(f"HTTP error {r.status_code}: {r.text}")
                time.sleep(2)
        except Exception as e:
            print("Retry after error:", e)
            time.sleep(2)
    return []

def fetch_search(niche):
    print(f"🔍 Searching for: {niche}")
    url = f"{API_BASE}/search"
    params = {"query": niche, "sort_by": "BEST_SELLERS", "country": "US", "page": 1}
    return [p["asin"] for p in safe_request(url, params)[:10]]

def fetch_details(asin):
    url = f"{API_BASE}/product-details"
    params = {"asin": asin, "country": "US"}
    return safe_request(url, params)

def fetch_reviews(asin):
    url = f"{API_BASE}/product-reviews"
    params = {"asin": asin, "country": "US", "page": 1, "sort_by": "TOP_REVIEWS"}
    return safe_request(url, params)

def build_html(niche, products):
    html = f"<html><head><title>Top 10 {niche.title()}</title></head><body><h1>Top 10 {niche.title()}</h1>"
    for p in products:
        title = p.get("title", "No title")
        img = (p.get("main_image") or {}).get("link", "")
        price = p.get("product_price", "N/A")
        rating = p.get("product_star_rating", "N/A")
        url = p.get("product_url", "#")
        reviews = p.get("reviews", [])
        review_html = "".join(f"<p>⭐ {r.get('rating','')} – {r.get('review_text','')[:120]}...</p>" for r in reviews[:2])
        html += f"<div><img src='{img}' width='200'/><h2>{title}</h2><p>💲{price} | ⭐ {rating}</p>{review_html}<a href='{url}?tag=scconnec0d-20'>Buy on Amazon</a></div><hr>"
    html += "</body></html>"
    out_dir = f"dist/{clean_slug(niche)}"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    return out_dir

def create_repo_and_push(niche, out_dir):
    repo_name = f"auto-niche-{clean_slug(niche)}"
    print(f"📦 Creating repo {repo_name}...")
    r = requests.post(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
        json={"name": repo_name, "private": False}
    )
    if r.status_code not in (200,201):
        print(f"GitHub repo creation failed: {r.text}")
        return
    subprocess.run(["git", "init"], cwd=out_dir)
    subprocess.run(["git", "branch", "-M", "main"], cwd=out_dir)
    subprocess.run(["git", "remote", "add", "origin", f"https://x-access-token:{GITHUB_TOKEN}@github.com/SC-Connections/{repo_name}.git"], cwd=out_dir)
    subprocess.run(["git", "add", "."], cwd=out_dir)
    subprocess.run(["git", "commit", "-m", "Initial niche deploy"], cwd=out_dir)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=out_dir)

def main():
    with open("niches.csv") as f:
        niches = [row[0].strip() for row in csv.reader(f) if row]
    for niche in niches:
        try:
            asins = fetch_search(niche)
            products = []
            for asin in asins:
                detail = fetch_details(asin)
                if isinstance(detail, list):
                    detail = detail[0] if detail else {}
                detail["reviews"] = fetch_reviews(asin)
                products.append(detail)
            out_dir = build_html(niche, products)
            create_repo_and_push(niche, out_dir)
        except Exception as e:
            print(f"❌ Failed for {niche}: {e}")

if __name__ == "__main__":
    main()
