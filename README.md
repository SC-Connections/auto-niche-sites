# Auto Niche Sites

One-button generator for 100+ niche static sites using a shared template, data from RapidAPI (Amazon), and GitHub Pages deploy (gh-pages branch).

## Features

Each generated site includes:
- **Quick Comparison Table** - Top 5 products with rankings
- **Detailed Product Reviews** - Full cards with pros/cons
- **Buyer's Guide** - Purchasing guidance for the niche
- **FAQ Section** - Common questions and answers
- **Trust Section** - Transparency and credibility statement

## How it works
- `niches.csv` lists the niches (one per line).
- `generate_sites.py` fetches Amazon data via RapidAPI and builds `/dist/<niche>/`.
- Each site uses the template in `site_template/` with Jinja2 rendering.
- GitHub Action deploys `/dist` to `gh-pages`.

## Template Structure

```
site_template/
├── index.html   # Jinja2 template with sections
├── style.css    # Responsive styles
└── script.js    # Client-side enhancements
```

## Run
Go to **Actions → Build & Deploy Niche Sites → Run workflow**.

## Environment Variables
- `RAPIDAPI_KEY` - Required for fetching Amazon product data
- `AMAZON_ASSOC_TAG` - Optional, adds affiliate tag to product URLs
- `RAPIDAPI_HOST` - Optional, defaults to configured endpoint
