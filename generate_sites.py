import os
import csv
import json
import requests
import shutil
import subprocess
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

# ---- UTILS ----
def fetch_amazon_data():
    """Fetch product deals from the new RapidAPI endpoint."""
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

def generate_site(niche, products):
    """Render an HTML site from template."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("index.html")

    niche_dir = os.path.join(OUTPUT_DIR, niche)
    os.makedirs(niche_dir, exist_ok=True)

    rendered = template.render(niche=niche, products=products)
    with open(os.path.join(niche_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(rendered)

def create_or_update_repo(niche):
    """Create or update a dedicated repo for the niche."""
    repo_name = f"{niche}-site"
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"

    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Create repo if it doesn’t exist
    res = requests.get(api_url, headers=headers)
    if res.status_code == 404:
        print(f"🚀 Creating GitHub repo: {repo_name}")
        create_res = requests.post(
            f"https://api.github.com/user/repos",
            headers=headers,
            json={"name": repo_name, "auto_init": True, "private": False}
        )
        if create_res.status_code not in (200, 201):
            print(f"❌ Failed to create repo: {create_res.text}")
            return

    # Push generated site
    repo_dir = os.path.join(OUTPUT_DIR, niche)
    subprocess.run(["git", "init"], cwd=repo_dir)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.email", "github-actions@github.com"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], cwd=repo_dir)
    subprocess.run(["git", "add", "."], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "Deploy site"], cwd=repo_dir)
    subprocess.run(
        [
            "git", "push", "--force",
            f"https://{GITHUB_USER}:{TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git",
            "main"
        ],
        cwd=repo_dir
    )
    print(f"✅ Deployed {niche} to https://github.com/{GITHUB_USER}/{repo_name}")

def main():
    print("⚙️ Starting site generation process...")

    # Ensure dist exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create .nojekyll file to prevent GitHub Pages from using Jekyll
    nojekyll_path = os.path.join(OUTPUT_DIR, ".nojekyll")
    with open(nojekyll_path, "w") as f:
        f.write("")
    print("✓ Created .nojekyll file to skip Jekyll processing")

    # Read niches.csv safely
    with open(NICHES_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "keyword" not in reader.fieldnames:
            raise KeyError("CSV must have a 'keyword' column.")
        for row in reader:
            niche = row["keyword"].strip()
            print(f"🔍 Fetching data for '{niche}'...")
            products = fetch_amazon_data()
            generate_site(niche, products)
            create_or_update_repo(niche)

    print("🎉 All niche sites generated and deployed!")

if __name__ == "__main__":
    main()
