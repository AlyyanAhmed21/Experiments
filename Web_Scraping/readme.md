# Web Scraper & Car Image Dataset Builder

This folder contains Python notebooks and scripts for two primary purposes:

1. **Quotes Scraper:** Collects quotes, authors, and related metadata from [quotes.toscrape.com](http://quotes.toscrape.com) (practice website for scraping).  
2. **Car Images Dataset Builder:** Builds a curated image dataset by scraping multiple free image sources (Unsplash, Pexels, Pixabay) and optionally adding manual URLs, with deduplication and filtering.

---

## 1. Quotes Scraper

### Purpose
- Demonstrates polite and structured web scraping.  
- Extracts quotes, authors, tags, and author details.  
- Saves the enriched dataset as CSV for further analysis.

### Key Features
- Pagination support to scrape multiple pages.  
- Author page enrichment: born date, location, short bio snippet.  
- Polite scraping: randomized delays, retry on failures, user-agent identification.  
- Quick statistics: top tags, counts, and previews.

### Usage
1. Install dependencies:

```bash
!pip install requests beautifulsoup4 pandas
Run the notebook quotes_scraper.ipynb.
```
Scraped results are saved to quotes_scraped.csv.

2. Car Images Dataset Builder
### Purpose
Create a high-quality dataset of car images using free image APIs.

Deduplicate images using SHA256 and perceptual hashing.

Enforce minimum resolution constraints and filter invalid images.

Save both images and metadata CSV for downstream tasks.

### Supported Sources
- Unsplash API

- Pexels API

- Pixabay API

- Optional manual URLs

### Features
- Randomized polite delays between requests.

- Image deduplication via perceptual hash (pHash) and SHA256.

- Automatic JPEG conversion and safe filenames.

- Metadata includes: source, URLs, dimensions, file size, hash values.

### Usage
Install dependencies:

```bash
!pip install requests pandas pillow imagehash tqdm
```
Update API keys for Unsplash, Pexels, and Pixabay in the notebook.

Run car_image_dataset_builder.ipynb.

#### Provide:

- Keyword (e.g., Porsche)

- Max images per source

- Max total images to save

- Minimum image dimensions

# Notes
Both scrapers are for learning and research purposes only.

Ensure compliance with API usage policies and robots.txt when scraping websites.

GPU is not required; a standard CPU environment like Google Colab works fine.

Frequent updates and modifications are encouraged to handle new sources or improve deduplication.

“Responsible scraping is about learning, exploring, and respecting the source.”
