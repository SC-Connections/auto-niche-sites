# Auto Niche Sites Generator

One-button generator for creating separate niche sites. Each niche gets its own dedicated GitHub repository with a Jekyll-based template, automated data fetching from Amazon via RapidAPI, and GitHub Pages deployment.

## How It Works

1. **Add Niches**: List your niches in `niches.csv` (one keyword per line)
2. **Run Generator**: Go to **Actions → 🧠 Auto Generate & Deploy Niche Sites → Run workflow**
3. **Sites Created**: For each niche, a new repository is automatically created with:
   - Complete Jekyll site structure
   - GitHub Actions workflow for fetching Amazon product data
   - Automatic deployment to GitHub Pages
   - Ready-to-use template for top 10 product lists

## Repository Structure

```
auto-niche-sites/
├── niches.csv              # List of niches to generate sites for
├── generate_sites.py       # Main generator script
├── site_template/          # Jekyll template for each site
│   ├── _config.yml        # Jekyll configuration
│   ├── _layouts/          # Page layouts
│   ├── _data/             # Product data storage
│   ├── _posts/            # Generated posts
│   ├── .github/           # Workflow automation
│   │   ├── workflows/     # GitHub Actions workflows
│   │   └── scripts/       # Data fetching scripts
│   └── index.md           # Homepage
└── .github/workflows/      # This repo's workflows
```

## Generated Site Features

Each generated site includes:

- **Automated Workflow**: Node.js-based workflow that:
  - Fetches live Amazon product data via RapidAPI
  - Creates Jekyll posts with product information
  - Commits and deploys automatically
  
- **Jekyll Structure**:
  - Top 10 product layout with images, prices, and ratings
  - Responsive design
  - SEO-friendly structure
  
- **Easy Content Creation**:
  - Run workflow with title and slug inputs
  - Automatic post generation
  - Instant deployment to GitHub Pages

## Setup

### Required Secrets

Add these secrets to your repository:
- `RAPIDAPI_KEY`: Your RapidAPI key for Amazon product data

### Running the Generator

1. Edit `niches.csv` with your desired niches:
   ```csv
   keyword
   bluetooth-earbuds
   gaming-microphones
   budget-laptops
   ```

2. Go to **Actions → 🧠 Auto Generate & Deploy Niche Sites → Run workflow**

3. The workflow will:
   - Create a new repository for each niche (e.g., `bluetooth-earbuds-site`)
   - Copy the Jekyll template to each repository
   - Configure GitHub Pages
   - Push the initial site structure

## Using Generated Sites

After generation, each site can be used independently:

1. Go to the generated repository (e.g., `SC-Connections/bluetooth-earbuds-site`)
2. Navigate to **Actions → Generate and Deploy Top 10 Post → Run workflow**
3. Enter:
   - **Title**: e.g., "Best Bluetooth Earbuds 2025"
   - **Slug**: e.g., "best-bluetooth-earbuds-2025"
4. The workflow will fetch Amazon data and create a new post

## Customization

- **Template**: Edit files in `site_template/` to customize all generated sites
- **Workflow**: Modify `.github/workflows/generate-sites.yml` for the generator behavior
- **Per-Site**: Each generated site can be customized independently after creation

## Workflow Details

The template workflow (used in each generated site) includes:

```yaml
# 1. Checkout repository
# 2. Install tooling (Node.js 20, mustache, axios)
# 3. Fetch Amazon data via RapidAPI
# 4. Create Jekyll post with data
# 5. Commit and deploy to GitHub Pages
```

This matches the workflow pattern specified in the requirements.

---

© 2025 SC Connections — Amazon Associate
