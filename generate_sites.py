import os
import csv
import requests
import json
import shutil
import subprocess
from jinja2 import Environment, FileSystemLoader

# === CONFIGURATION ===
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")  # required for pushing per-niche repos
TEMPLATE_DIR = "site_template"
DIST_DIR = "dist"
BASE_REPO = "SC-Connections"  # change this if under a different org/user
API_URL = "https://amazon-real-time-api.p.rapidapi.com/deals"

# === PREP ENVIRONMENT ===
os.makedirs(DIST_DIR, exist_ok=True)

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
template = env.get_template("index.html")

def fetch_amazon_data(niche):
    """
    Fetch Amazon deals for a specific niche using the RapidAPI endpoint.
    """
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "amazon-real-time-api.p.rapidapi.com"
    }
    params = {
        "domain": "US",
        "node_id": "16310101"  # general Electronics node — adjust per niche later if needed
    }

    print(f"🔍 Fetching deals for '{niche}'...")
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if "data" not in data:
            print(f"⚠️ No valid data returned for {niche}")
            return []
        return data["data"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {niche}: {e}")
        return []


def create_site(niche, products):
    """
    Build static site files for the given niche.
    """
    niche_dir = os.path.join(DIST_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)

    html_content = template.render(niche=niche, products=products)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Generated site for '{niche}' → {niche_dir}")


def push_to_repo(niche):
    """
    Creates or updates a separate GitHub repo for each niche.
    Requires GH_TOKEN with `repo` permissions.
    """
    if not GH_TOKEN:
        print("⚠️ GH_TOKEN not set. Skipping repo push.")
        return

    repo_name = f"{niche}-site"
    print(f"🚀 Creating/updating GitHub repo: {repo_name}")

    # Create repo if it doesn't exist
    subprocess.run([
        "curl", "-H", f"Authorization: token {GH_TOKEN}",
        "-d", json.dumps({"name": repo_name, "auto_init": True, "private": False}),
        f"https://api.github.com/user/repos"
    ])

    repo_url = f"https://{GH_TOKEN}@github.com/{BASE_REPO}/{repo_name}.git"
    niche_path = os.path.join(DIST_DIR, niche)

    # Initialize and push the generated site
    subprocess.run(["git", "init"], cwd=niche_path)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=niche_path)
    subprocess.run(["git", "add", "."], cwd=niche_path)
    subprocess.run(["git", "commit", "-m", "Deploy niche site"], cwd=niche_path)
    subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=niche_path)
    subprocess.run(["git", "push", "-f", "origin", "main"], cwd=niche_path)

    print(f"✅ Deployed {niche} to https://github.com/{BASE_REPO}/{repo_name}")


def main():
    print("⚙️ Starting site generation process...")

    with open("niches.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            niche = row.get("keyword") or row.get("niche")
            if not niche:
                continue

            products = fetch_amazon_data(niche)
            create_site(niche, products)
            push_to_repo(niche)

    print("🎉 All niche sites generated and deployed!")


if __name__ == "__main__":
    main()
