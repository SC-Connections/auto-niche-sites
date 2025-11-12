# Auto Niche Sites

One-button generator for 100+ niche static sites using a shared template, data from RapidAPI (Amazon), and GitHub Pages deploy (gh-pages branch).

## How it works
- `niches.csv` lists the niches.
- `generate_sites.py` fetches Amazon data via RapidAPI and builds `/dist/<niche>/`.
- GitHub Action deploys `/dist` to `gh-pages`.

## Run
Go to **Actions → Build & Deploy Niche Sites → Run workflow**.
