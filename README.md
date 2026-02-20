# SkinWise Monorepo (Next.js + FastAPI + Postgres)

SkinWise is an MVP that captures skincare intake data and returns **exactly 5 recommendations** with transparent scoring and citations.

## Structure

- `frontend/` — Next.js PWA UI (intake, results, admin)
- `backend/` — FastAPI API + scoring engine
- `db/migrations/` — baseline SQL schema
- `db/seed/` — seed data for categories, diagnoses, weights, flag rules, evidence stubs, and 60 products
- `docker-compose.yml` — local full stack startup

## Run locally (Docker)

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Admin view: `http://localhost:3000/admin` (MVP basic auth defaults: `admin/admin`)
- Backend: `http://localhost:8000`

## API Endpoints

- `POST /intake`
- `POST /recommendations` (supports `overall` and `category` modes; always returns 5)
- `GET /products`
- `POST /products/import_csv`
- `PATCH /products/{id}`
- `GET/PATCH /admin/weights`
- `GET/PATCH /admin/flag_rules`
- `GET/POST /admin/evidence_snippets`

## Quick checks

```bash
cd backend && pytest -q
cd backend && python -m compileall app
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

- Composite score is computed as `Fit (0-45) + Safety (0-25) + Evidence (0-20) + Value (0-10)`.
- Evidence multipliers: `A=1.0`, `B=0.7`, `C=0.4`.
- Value is percentile by `cost_per_ml` within category.
- Sunscreen is forcibly included in overall mode if any of photodamage/melasma/rosacea/sun exposure is > 0.
- All scoring is heuristic and intended as a product-ranking prototype.
- Nationality/locale should be used for **availability and language only** (not biological inference).
