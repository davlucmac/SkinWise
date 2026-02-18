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
  - Avoid flags
  - Evidence strength + citations
  - “Why it fits” summary

## Project Structure

- `index.html` – page layout and intake/admin/results sections
- `styles.css` – UI styling
- `app.js` – intake capture, weighting, scoring, and rendering logic

## Run Locally

Because this is a static app, any simple web server will work.

```bash
python3 -m http.server 4173
```

Then open:

- `http://localhost:4173`

## Quick Validation

```bash
node --check app.js
```

## Notes

- All scoring is heuristic and intended as a product-ranking prototype.
- Nationality/locale should be used for **availability and language only** (not biological inference).
