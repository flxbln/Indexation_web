# TP_ENSAI — Indexation et moteur de recherche

## TP1 — Web Crawler

This project implements a Python crawler capable of browsing a website, prioritizing product pages, and storing the extracted results in a JSON file.

### Usage

```bash
python TP1.py
```

## TP2 – Inverted Indexes

### Description
This tool processes product data from JSONL files and generates multiple specialized indexes to enable fast searching across product titles, descriptions, brands, origins, and customer reviews.

### Requirements
```bash
pip install pandas nltk
```

### Usage

```bash
python TP2/TP2.py
```

The script reads `TP2/products.jsonl` and creates all indexes in the `TP2/indexes/` directory.

### Input Format

The input must be a JSONL file where each line contains a product object:

```json
{
  "url": "https://web-scraping.dev/product/1",
  "title": "Box of Chocolate Candy",
  "description": "HIndulge your sweet tooth with our Box of Chocolate Candy....",
  "product_features": {
    "materials": "Premium quality chocolate",
    "flavors": "Available in Orange and Cherry flavors"
  },
  "product_reviews": {
    "date": "2022-07-22",
    "id": "chocolate-candy-box-1",
    ...
  }
}
```

### Output Files


The system generates five JSON index files:

### 1. `title_index.json`
Positional inverted index for product titles:
```json
{
  "webscrapingdev": {
    "https://web-scraping.dev/products": [0],
    "https://web-scraping.dev/products?page=1": [3],
    ...
  }
}
```

### 2. `description_index.json`
Positional inverted index for product descriptions (same structure as title index)

### 3. `brand_index.json`
Maps brands to product URLs:
```json
{
  "ChocoDelight": [
    "https://web-scraping.dev/product/1",
    "https://web-scraping.dev/product/13",
    ...
  ]
}
```

### 4. `origin_index.json`
Maps countries of origin to product URLs (same structure as brand index)

### 5. `reviews_index.json`
Aggregated review statistics per product:
```json
{
  "https://web-scraping.dev/products": {
    "review_count": 0,
    "avg_rating": 0,
    "latest_rating": null
  },
  ...
}
```

### Text Processing Pipeline

1. Convert text to lowercase
2. Split on whitespace
3. Remove punctuation and special characters
4. Filter out English stopwords
5. Return cleaned tokens





## TP3 – Search Engine Implementation

### Description
This project implements a product search engine using inverted positional indexes, BM25 ranking algorithm, and query expansion through synonyms. The engine is designed to search through e-commerce products with support for multi-criteria queries, geographic filtering, and variant handling.


### Requirements
```bash
pip install nltk
```

## Usage
```bash
python TP3/TP3.py
```


## Architecture

### Object-Oriented Design

The project is structured using clean object-oriented principles with clear separation of concerns:

```
IndexLoader          → Handles index and product data loading
DocumentFilter       → Implements document filtering strategies
BM25Calculator       → Manages BM25 scoring algorithm
ExactMatcher        → Handles exact phrase matching
DocumentRanker      → Combines multiple signals for final ranking
SearchEngine        → Main orchestrator for search operations
ResultFormatter     → Formats results as structured JSON
```

## Output
Search results can be saved as JSON files:
```
TP3/results/<query>.json
```

## Notes

### Strengths 
1. **Excellent recall**: All relevant products are found
2. **Effective synonym expansion**: Works well for countries
3. **Well-implemented BM25**: Good TF-IDF weighting
4. **Exact match rewarded**: 50-point bonus works well
5. **Product/variant hierarchy respected**: Main products ranked higher than variants

### Areas for Improvement 
1. **Variant differentiation**: Scores sometimes too close between variants
2. **Variant attribute weights**: Color and size could have more impact
3. **Score variance**: Some queries produce very homogeneous scores
4. **Filtering irrelevant variants**: "White" variants appear in "black" searches


## Authors

- Felix Blain
- Created for web indexing coursework at ENSAI.
