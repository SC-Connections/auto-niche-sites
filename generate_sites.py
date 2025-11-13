import os
import csv
import json
import time
import requests
import subprocess
from jinja2 import Environment, FileSystemLoader

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "amazon-real-time-api.p.rapidapi.com"
GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "SC-Connections"

# Each niche will create its own repo, e.g., bluetooth-earbuds -> auto-bluetooth-earbuds
BASE_REPO_PREFIX = "auto-"

TEMPLATE_DIR = "site_template"
DIST_DIR = "dist"

# Ensure directories exist
os.makedirs(DIST_DIR, exist_ok=True)

# Load template
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("index.html")

def fetch_amazon_deals(keyword):
    """Fetch deals for a keyword from RapidAPI."""
    url = "https://amazon-real-time-api.p.rapidapi.com/deals"
    querystring = {"domain": "US", "node_id": "16310101"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    print(f"🔍 Fetching deals for '{keyword}'...")
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        if response.status_code != 200:
            print(f"❌ API error {response.status_code}: {response.text}")
            return []

        data = response.json()
        # Each deal has title, url, image, price, etc.
        items = data.get("data", [])
        print(f"✅ Retrieved {len(items)} deals for {keyword}")
        return items

    except Exception as e:
        print(f"❌ Error fetching data for {keyword}: {e}")
        return []

def create_github_repo(niche):
    """Create or update a GitHub repository for this niche."""
    repo_name = f"{BASE_REPO_PREFIX}{niche}"
    url = f"https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {"name": repo_name, "private": False, "auto_init": True, "description": f"Auto niche site for {niche}"}
    print(f"🛠️ Creating/updating repo {repo_name}...")

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"✅ Repo {repo_name} created successfully.")
        elif response.status_code == 422:
            print(f"ℹ️ Repo {repo_name} already exists, skipping creation.")
        else:
            print(f"⚠️ Repo creation error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to create repo for {niche}: {e}")

    return repo_name

def generate_site(niche, products):
    """Generate static HTML site for a given niche."""
    if not products:
        print(f"⚠️ No data for {niche}, skipping.")
        return

    niche_dir = os.path.join(DIST_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)

    output = template.render(niche=niche, products=products)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ Site generated for {niche} → {niche_dir}/index.html")

def main():
    print("⚙️ Starting site generation (one repo per niche)...")
    with open("niches.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "keyword" not in reader.fieldnames:
            print("❌ CSV missing 'keyword' column — check file header.")
            return

        for row in reader:
            keyword = row["keyword"].strip()
            if not keyword:
                continue

            deals = fetch_amazon_deals(keyword)
            generate_site(keyword, deals)

            # Create repo for niche
            repo_name = create_github_repo(keyword)

            # Commit + push site to repo
            try:
                subprocess.run(["git", "init"], cwd=os.path.join(DIST_DIR, keyword), check=True)
                subprocess.run(["git", "add", "."], cwd=os.path.join(DIST_DIR, keyword), check=True)
                subprocess.run(["git", "commit", "-m", f"Deploy site for {keyword}"], cwd=os.path.join(DIST_DIR, keyword), check=True)
                subprocess.run(["git", "branch", "-M", "main"], cwd=os.path.join(DIST_DIR, keyword), check=True)
                subprocess.run([
                    "git", "remote", "add", "origin",
                    f"https://{USERNAME}:{GITHUB_TOKEN}@github.com/{USERNAME}/{repo_name}.git"
                ], cwd=os.path.join(DIST_DIR, keyword), check=True)
                subprocess.run(["git", "push", "-u", "origin", "main", "--force"], cwd=os.path.join(DIST_DIR, keyword), check=True)
                print(f"🚀 Deployed {keyword} to https://{USERNAME}.github.io/{repo_name}/")
            except Exception as e:
                print(f"⚠️ Git push failed for {keyword}: {e}")

            time.sleep(3)

    print("🎉 All niche repos generated and deployed successfully.")

if __name__ == "__main__":
    main()
