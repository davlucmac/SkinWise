# SkinWise

SkinWise is a lightweight browser app for collecting skincare intake data and generating **exactly 5 product recommendations** using evidence-weighted scoring.

## Features

- Intake form for:
  - Age, sex, skin type, diagnoses, symptoms, sensitivities
  - Fitzpatrick I–VI (with helper mapping when unknown)
  - Severity scales (photodamage, melasma, rosacea, acne, wrinkles, laxity, sun/screen exposure)
  - Free-text client concern
  - Budget by max price and/or max $/mL
- Admin-editable Layer A feature weights (0–10)
- Composite scoring (0–100):
  - Fit (0–45)
  - Safety/Avoid (0–25)
  - Evidence (0–20)
  - Value (0–10)
- Recommendation cards include:
  - Price, size, $/mL
  - Key actives
  - PDP URL
  - Avoid flags
  - Evidence strength + citations
  - “Why it fits” summary

## Project Structure

- `index.html` – page layout and intake/admin/results sections
- `styles.css` – UI styling
- `app.js` – intake capture, weighting, scoring, and rendering logic
- `scripts/collect_products.py` – product ingestion/normalization pipeline
- `data/products.seed.json` – base catalog data
- `data/source_feeds/*.json` – source feed drop folder (EWG, Yucca, Amazon, etc.)
- `data/products.catalog.json` – generated catalog consumed by the app

## Product Collection Pipeline (EWG, Yucca, Amazon, Trusted Sources)

SkinWise includes a source ingestion pipeline that standardizes incoming product records and ensures each record includes a valid PDP URL.

### 1) Add source feed files

Drop JSON files in `data/source_feeds/` (examples are included):

- `ewg.sample.json`
- `yucca.sample.json`
- `amazon.sample.json`

Each file should be an array of source rows with this schema:

```json
{
  "source_product_id": "unique-source-id",
  "name": "Product Name",
  "brand": "Brand Name",
  "pdp_url": "https://...",
  "category": "sunscreen|treatment|retinoid|moisturizer|exfoliant|cleanser",
  "price": 19.99,
  "size_ml": 50,
  "actives": ["niacinamide"],
  "avoid_flags": ["fragrance"],
  "irritancy": 2,
  "pih_safe": true,
  "evidence": {"acne": "moderate"},
  "citations": ["Source citation"],
  "trusted": true
}
```

### 2) Run the collector

```bash
python3 scripts/collect_products.py
```

This script:

- Reads `data/products.seed.json`
- Ingests all `data/source_feeds/*.json`
- Keeps only rows with `trusted: true`
- Requires a valid `http/https` PDP URL (`pdp_url`)
- Normalizes records into app catalog format
- De-duplicates by `(source, source_product_id)`
- Writes `data/products.catalog.json`

### 3) Launch app

```bash
python3 -m http.server 4173
```

Then open:

- `http://localhost:4173`

The app automatically loads `data/products.catalog.json` and falls back to bundled data if loading fails.

## Quick Validation

```bash
node --check app.js
python3 scripts/collect_products.py
```

## Notes

- All scoring is heuristic and intended as a product-ranking prototype.
- Nationality/locale should be used for **availability and language only** (not biological inference).
- Respect each source’s Terms of Use when collecting or syncing product data.
