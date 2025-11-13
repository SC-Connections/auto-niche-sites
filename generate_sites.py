import os, csv, requests, json, shutil, subprocess, re

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}

API_BASE = "https://real-time-amazon-data.p.rapidapi.com"

def clean_slug(name):
    return re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-')

def fetch_search(niche):
    url = f"{API_BASE}/search"
    params = {"query": niche, "sort_by": "BEST_SELLERS", "country": "US", "page": 1}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json().get("data", [])
    return [p["asin"] for p in data[:10]]

def fetch_details(asin):
    url = f"{API_BASE}/product-details"
    params = {"asin": asin, "country": "US"}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json().get("data", {})

def fetch_reviews(asin):
    url = f"{API_BASE}/product-reviews"
    params = {"asin": asin, "country": "US", "page": 1, "sort_by": "TOP_REVIEWS"}
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code != 200:
        return []
    return r.json().get("data", [])

def build_html(niche, products):
    template_path = "site_template/index.html"
    with open(template_path) as f:
        template = f.read()

    product_html = ""
    for p in products:
        title = p.get("title", "No title")
        img = (p.get("main_image") or {}).get("link", "")
        price = p.get("product_price", "N/A")
        rating = p.get("product_star_rating", "N/A")
        url = p.get("product_url", "#")
        asin = p.get("asin", "")
        reviews = p.get("reviews", [])
        review_html = "".join(
            f"<p>⭐️ {r.get('rating', '')} – {r.get('review_text', '')}</p>"
            for r in reviews[:3]
        )
        product_html += f"""
        <div class='product'>
          <img src='{img}' alt='{title}'/>
          <h2>{title}</h2>
          <p><strong>Price:</strong> {price}</p>
          <p><strong>Rating:</strong> {rating}</p>
          {review_html}
          <a href='{url}?tag=scconnec0d-20' class='buy-btn'>Buy on Amazon</a>
        </div>
        """

    output = template.replace("{{NICHE}}", niche.title()).replace("{{PRODUCTS}}", product_html)
    out_dir = f"dist/{clean_slug(niche)}"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(output)
    return out_dir

def create_repo_and_push(niche, out_dir):
    repo_name = f"auto-niche-{clean_slug(niche)}"
    print(f"Creating repo {repo_name} ...")
    res = requests.post(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        json={"name": repo_name, "private": False}
    )
    if res.status_code not in (200,201):
        print("Repo creation failed:", res.text)
        return
    subprocess.run(["git", "init"], cwd=out_dir)
    subprocess.run(["git", "branch", "-M", "main"], cwd=out_dir)
    subprocess.run(["git", "remote", "add", "origin", f"https://x-access-token:{GITHUB_TOKEN}@github.com/SC-Connections/{repo_name}.git"], cwd=out_dir)
    subprocess.run(["git", "add", "."], cwd=out_dir)
    subprocess.run(["git", "commit", "-m", "Initial niche deploy"], cwd=out_dir)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=out_dir)

def main():
    with open("niches.csv") as f:
        reader = csv.reader(f)
        niches = [row[0].strip() for row in reader if row]
    for niche in niches:
        print(f"Building site for {niche}...")
        try:
            asins = fetch_search(niche)
            products = []
            for asin in asins:
                details = fetch_details(asin)
                details["reviews"] = fetch_reviews(asin)
                products.append(details)
            out_dir = build_html(niche, products)
            create_repo_and_push(niche, out_dir)
        except Exception as e:
            print(f"Failed for {niche}: {e}")

if __name__ == "__main__":
    main()
