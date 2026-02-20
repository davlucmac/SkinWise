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
```

## Notes

- Composite score is computed as `Fit (0-45) + Safety (0-25) + Evidence (0-20) + Value (0-10)`.
- Evidence multipliers: `A=1.0`, `B=0.7`, `C=0.4`.
- Value is percentile by `cost_per_ml` within category.
- Sunscreen is forcibly included in overall mode if any of photodamage/melasma/rosacea/sun exposure is > 0.
