import os
import csv
import json
import requests
import shutil
import subprocess
import time

# ---- CONFIG ----
TEMPLATE_DIR = "site_template"
OUTPUT_DIR = "dist"
NICHES_FILE = "niches.csv"
GITHUB_USER = "SC-Connections"
TOKEN = os.getenv("GITHUB_TOKEN")

# ---- UTILS ----
def generate_jekyll_site(niche, niche_title):
    """Create a Jekyll site from template."""
    niche_slug = niche.lower().replace(" ", "-")
    niche_dir = os.path.join(OUTPUT_DIR, niche_slug)
    
    # Remove existing directory if it exists
    if os.path.exists(niche_dir):
        shutil.rmtree(niche_dir)
    
    # Copy template directory
    print(f"📁 Copying template to {niche_dir}...")
    shutil.copytree(TEMPLATE_DIR, niche_dir)
    
    # Replace placeholders in _config.yml
    config_path = os.path.join(niche_dir, "_config.yml")
    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()
    
    config_content = config_content.replace("{{NICHE_TITLE}}", niche_title)
    config_content = config_content.replace("{{NICHE_SLUG}}", niche_slug)
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    # Replace placeholders in README.md
    readme_path = os.path.join(niche_dir, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()
    
    readme_content = readme_content.replace("{{NICHE_TITLE}}", niche_title)
    readme_content = readme_content.replace("{{NICHE_SLUG}}", niche_slug)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Replace placeholders in index.md
    index_path = os.path.join(niche_dir, "index.md")
    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()
    
    index_content = index_content.replace("{{NICHE_TITLE}}", niche_title)
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print(f"✅ Generated Jekyll site for {niche_title}")
    return niche_dir, niche_slug

def create_or_update_repo(niche_slug, niche_title, niche_dir):
    """Create or update a dedicated repo for the niche."""
    repo_name = f"{niche_slug}-site"
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"

    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Check if repo exists
    res = requests.get(api_url, headers=headers)
    
    if res.status_code == 404:
        # Create repo if it doesn't exist
        print(f"🚀 Creating GitHub repo: {repo_name}")
        create_res = requests.post(
            f"https://api.github.com/user/repos",
            headers=headers,
            json={
                "name": repo_name,
                "description": f"Top 10 {niche_title} products from Amazon",
                "homepage": f"https://{GITHUB_USER.lower()}.github.io/{repo_name}",
                "private": False,
                "has_issues": True,
                "has_projects": False,
                "has_wiki": False
            }
        )
        if create_res.status_code not in (200, 201):
            print(f"❌ Failed to create repo: {create_res.text}")
            return False
        
        # Wait a bit for repo to be fully created
        time.sleep(2)
    else:
        print(f"📦 Repo {repo_name} already exists, updating...")

    # Initialize git and push
    print(f"📤 Pushing to {repo_name}...")
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=niche_dir, check=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=niche_dir, check=True)
    subprocess.run(["git", "config", "user.email", "github-actions@github.com"], cwd=niche_dir, check=True)
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], cwd=niche_dir, check=True)
    
    # Add all files and commit
    subprocess.run(["git", "add", "."], cwd=niche_dir, check=True)
    subprocess.run(["git", "commit", "-m", f"Initialize {niche_title} niche site"], cwd=niche_dir, check=True)
    
    # Push to remote
    remote_url = f"https://{TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
    subprocess.run(
        ["git", "push", "--force", remote_url, "main"],
        cwd=niche_dir,
        check=True
    )
    
    print(f"✅ Deployed {niche_title} to https://github.com/{GITHUB_USER}/{repo_name}")
    
    # Enable GitHub Pages with GitHub Actions source
    enable_pages(repo_name, headers)
    
    return True

def enable_pages(repo_name, headers):
    """Enable GitHub Pages for the repository using GitHub Actions."""
    pages_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/pages"
    
    # Try to create or update Pages configuration
    print(f"🌐 Enabling GitHub Pages for {repo_name}...")
    
    pages_config = {
        "source": {
            "branch": "main",
            "path": "/"
        },
        "build_type": "workflow"
    }
    
    # First try to create
    res = requests.post(pages_url, headers=headers, json=pages_config)
    
    if res.status_code == 409:
        # Pages already exists, try to update
        res = requests.put(pages_url, headers=headers, json=pages_config)
    
    if res.status_code in (200, 201, 204):
        print(f"✅ GitHub Pages enabled for {repo_name}")
    else:
        print(f"⚠️ Could not enable GitHub Pages automatically (status {res.status_code})")
        print(f"   Please enable it manually in the repository settings")

def add_rapidapi_secret(repo_name, headers):
    """Add RAPIDAPI_KEY secret to the repository."""
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
        print(f"⚠️ RAPIDAPI_KEY not found in environment, skipping secret creation")
        return
    
    print(f"🔐 Adding RAPIDAPI_KEY secret to {repo_name}...")
    
    # Get the repository's public key for encrypting secrets
    pubkey_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/actions/secrets/public-key"
    pubkey_res = requests.get(pubkey_url, headers=headers)
    
    if pubkey_res.status_code != 200:
        print(f"⚠️ Could not get public key for repo (status {pubkey_res.status_code})")
        return
    
    try:
        from nacl import encoding, public
        
        pubkey_data = pubkey_res.json()
        public_key = public.PublicKey(pubkey_data["key"].encode("utf-8"), encoding.Base64Encoder())
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(rapidapi_key.encode("utf-8"))
        encrypted_value = encoding.Base64Encoder.encode(encrypted).decode("utf-8")
        
        # Create or update the secret
        secret_url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/actions/secrets/RAPIDAPI_KEY"
        secret_data = {
            "encrypted_value": encrypted_value,
            "key_id": pubkey_data["key_id"]
        }
        
        secret_res = requests.put(secret_url, headers=headers, json=secret_data)
        
        if secret_res.status_code in (201, 204):
            print(f"✅ RAPIDAPI_KEY secret added to {repo_name}")
        else:
            print(f"⚠️ Could not add secret (status {secret_res.status_code})")
    except ImportError:
        print(f"⚠️ PyNaCl not installed, cannot encrypt secrets")
        print(f"   Install with: pip install pynacl")
        print(f"   Please add RAPIDAPI_KEY secret manually in the repository settings")
    except Exception as e:
        print(f"⚠️ Error adding secret: {e}")

def main():
    print("⚙️ Starting site generation process...")
    
    if not TOKEN:
        print("❌ GITHUB_TOKEN not found in environment!")
        return

    # Ensure dist exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Read niches.csv safely
    with open(NICHES_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "keyword" not in reader.fieldnames:
            raise KeyError("CSV must have a 'keyword' column.")
        
        niches_processed = []
        
        for row in reader:
            niche = row["keyword"].strip()
            if not niche:
                continue
                
            # Use the niche as both slug and title (can be improved)
            niche_title = niche.replace("-", " ").title()
            
            print(f"\n{'='*60}")
            print(f"🔍 Processing niche: {niche_title}")
            print(f"{'='*60}\n")
            
            # Generate Jekyll site
            niche_dir, niche_slug = generate_jekyll_site(niche, niche_title)
            
            # Create/update GitHub repository
            if create_or_update_repo(niche_slug, niche_title, niche_dir):
                niches_processed.append(niche_title)
                print(f"\n✅ Successfully processed: {niche_title}")
            else:
                print(f"\n❌ Failed to process: {niche_title}")

    print(f"\n{'='*60}")
    print(f"🎉 Site generation complete!")
    print(f"{'='*60}")
    print(f"\nProcessed {len(niches_processed)} niche(s):")
    for niche in niches_processed:
        print(f"  ✓ {niche}")
    print()

if __name__ == "__main__":
    main()
