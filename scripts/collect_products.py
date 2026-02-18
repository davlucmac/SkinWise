#!/usr/bin/env python3
"""
Collect product feeds from trusted sources and build SkinWise catalog.

Inputs:
  - JSON files in data/source_feeds/*.json
  - Optional existing catalog in data/products.seed.json

Output:
  - data/products.catalog.json

Rules:
  - PDP URL is required and must be http/https.
  - Source is normalized from filename (ewg, yucca, amazon, ...).
  - Only records marked trusted=true are included.
  - Product dedupe key: source + sourceProductId.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

VALID_EVIDENCE = {"strong", "moderate", "limited"}


@dataclass
class Product:
  id: str
  name: str
  brand: str
  source: str
  sourceProductId: str
  pdpUrl: str
  category: str
  price: float
  sizeMl: float
  actives: list[str]
  avoids: list[str]
  irritancy: int
  pihSafe: bool
  evidence: dict[str, str]
  citations: list[str]


def slugify(value: str) -> str:
  return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def is_valid_http_url(value: str) -> bool:
  try:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
  except Exception:
    return False


def normalize_record(raw: dict[str, Any], source: str) -> Product | None:
  if not raw.get("trusted", False):
    return None

  pdp_url = str(raw.get("pdp_url", "")).strip()
  if not is_valid_http_url(pdp_url):
    raise ValueError(f"Invalid or missing pdp_url: {pdp_url!r} ({source})")

  evidence_raw = raw.get("evidence") or {}
  evidence = {
    str(k): str(v)
    for k, v in evidence_raw.items()
    if str(v) in VALID_EVIDENCE
  }

  if not evidence:
    evidence = {"skinType": "limited"}

  name = str(raw.get("name", "")).strip()
  source_product_id = str(raw.get("source_product_id", "")).strip()
  if not name or not source_product_id:
    raise ValueError(f"Missing required name/source_product_id in {source}")

  product_id = f"{slugify(name)}-{slugify(source)}-{slugify(source_product_id)}"

  return Product(
    id=product_id,
    name=name,
    brand=str(raw.get("brand", "Unknown Brand")).strip() or "Unknown Brand",
    source=source,
    sourceProductId=source_product_id,
    pdpUrl=pdp_url,
    category=str(raw.get("category", "treatment")).strip() or "treatment",
    price=float(raw.get("price", 0) or 0),
    sizeMl=float(raw.get("size_ml", 0) or 0),
    actives=[str(x) for x in raw.get("actives", [])],
    avoids=[str(x) for x in raw.get("avoid_flags", [])],
    irritancy=max(0, min(4, int(raw.get("irritancy", 2)))),
    pihSafe=bool(raw.get("pih_safe", True)),
    evidence=evidence,
    citations=[str(x) for x in raw.get("citations", [f"{source} PDP"])],
  )


def load_json_list(path: Path) -> list[dict[str, Any]]:
  payload = json.loads(path.read_text())
  if not isinstance(payload, list):
    raise ValueError(f"Expected list in {path}")
  return payload


def read_seed_products(seed_path: Path) -> list[Product]:
  if not seed_path.exists():
    return []
  seed_payload = load_json_list(seed_path)
  parsed: list[Product] = []
  for row in seed_payload:
    parsed.append(Product(
      id=row["id"],
      name=row["name"],
      brand=row.get("brand", "Unknown Brand"),
      source=row.get("source", "internal"),
      sourceProductId=row.get("sourceProductId", row["id"]),
      pdpUrl=row["pdpUrl"],
      category=row.get("category", "treatment"),
      price=float(row.get("price", 0) or 0),
      sizeMl=float(row.get("sizeMl", 0) or 0),
      actives=[str(x) for x in row.get("actives", [])],
      avoids=[str(x) for x in row.get("avoids", [])],
      irritancy=int(row.get("irritancy", 2)),
      pihSafe=bool(row.get("pihSafe", True)),
      evidence={str(k): str(v) for k, v in (row.get("evidence") or {}).items()},
      citations=[str(x) for x in row.get("citations", [])],
    ))
  return parsed


def build_catalog(seed: list[Product], feed_glob: str) -> list[Product]:
  deduped: dict[tuple[str, str], Product] = {
    (p.source, p.sourceProductId): p for p in seed
  }

  for file_name in sorted(glob.glob(feed_glob)):
    path = Path(file_name)
    source = path.stem.split(".")[0].lower()
    rows = load_json_list(path)
    for raw in rows:
      product = normalize_record(raw, source)
      if product is None:
        continue
      deduped[(product.source, product.sourceProductId)] = product

  catalog = sorted(deduped.values(), key=lambda p: (p.source, p.name.lower()))
  return catalog


def write_catalog(products: list[Product], output_path: Path) -> None:
  output_path.write_text(json.dumps([asdict(p) for p in products], indent=2) + "\n")


def main() -> None:
  parser = argparse.ArgumentParser(description="Build SkinWise product catalog from trusted feeds")
  parser.add_argument("--seed", default="data/products.seed.json")
  parser.add_argument("--feeds", default="data/source_feeds/*.json")
  parser.add_argument("--output", default="data/products.catalog.json")
  args = parser.parse_args()

  seed = read_seed_products(Path(args.seed))
  catalog = build_catalog(seed=seed, feed_glob=args.feeds)
  write_catalog(catalog, Path(args.output))
  print(f"Wrote {len(catalog)} products to {args.output}")


if __name__ == "__main__":
  main()
