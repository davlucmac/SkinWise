from uuid import uuid4
import csv
from io import StringIO
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import BASIC_ADMIN_USER, BASIC_ADMIN_PASSWORD
from app.schemas import (
    IntakeCreate, IntakeResponse, RecoRequest, RecommendationsResponse, RecommendationCard,
    WeightUpdate, FlagRuleUpdate, ProductPatch, EvidenceSnippetCreate,
)
from app.services.scoring import compute_recommendations

app = FastAPI(title="SkinWise API")
security = HTTPBasic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


def admin_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != BASIC_ADMIN_USER or credentials.password != BASIC_ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/intake", response_model=IntakeResponse)
def create_intake(payload: IntakeCreate, db: Session = Depends(get_db)):
    intake_id = uuid4()
    db.execute(text("""
      INSERT INTO intake_profile (id, age, sex, fitzpatrick_type, locale, skin_type, skin_problems_text, primary_concern_text,
      photodamage, melasma_level, rosacea_level, acne_level, wrinkles_level, laxity_level, sun_exposure_level, screen_exposure_level,
      acne_type, pregnant_or_bf, budget_max_price, budget_max_cost_per_ml)
      VALUES (:id, :age, :sex, :fitzpatrick_type, :locale, :skin_type, :skin_problems_text, :primary_concern_text,
      :photodamage, :melasma_level, :rosacea_level, :acne_level, :wrinkles_level, :laxity_level, :sun_exposure_level, :screen_exposure_level,
      :acne_type, :pregnant_or_bf, :budget_max_price, :budget_max_cost_per_ml)
    """), {"id": str(intake_id), **payload.model_dump(exclude={"diagnosis_codes", "avoid_codes"})})

    for code in payload.diagnosis_codes:
        db.execute(text("""
          INSERT INTO intake_profile_diagnosis (intake_profile_id, diagnosis_id)
          SELECT :intake_id, id FROM diagnosis WHERE code=:code
          ON CONFLICT DO NOTHING
        """), {"intake_id": str(intake_id), "code": code})
    for code in payload.avoid_codes:
        db.execute(text("""
          INSERT INTO intake_profile_avoid (intake_profile_id, ingredient_avoid_rule_id)
          SELECT :intake_id, id FROM ingredient_avoid_rule WHERE code=:code
          ON CONFLICT DO NOTHING
        """), {"intake_id": str(intake_id), "code": code})
    db.commit()
    return IntakeResponse(intake_profile_id=intake_id)


@app.post("/recommendations", response_model=RecommendationsResponse)
def recommend(payload: RecoRequest, db: Session = Depends(get_db)):
    try:
        rows, weights = compute_recommendations(db, payload.intake_profile_id, payload.mode, payload.category_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    run_id = uuid4()
    category_id = None
    if payload.category_code:
        category_id = db.execute(text("SELECT id FROM product_category WHERE code=:c"), {"c": payload.category_code}).scalar()

    db.execute(text("INSERT INTO recommendation_run (id, intake_profile_id, mode, requested_category_id, weights_snapshot) VALUES (:id,:intake,:mode,:cat,:weights)"),
               {"id": str(run_id), "intake": str(payload.intake_profile_id), "mode": payload.mode, "cat": category_id, "weights": weights})

    cards = []
    for idx, row in enumerate(rows, start=1):
        total, fit, safety, evidence, value, strength, triggered, p = row
        why = f"Aligned for {p['category']} with fit/safety/evidence/value balance."
        citations = [{"title": "MVP evidence snippet", "url": "https://example.org"}]
        db.execute(text("""
          INSERT INTO recommendation_item (recommendation_run_id, rank, product_id, score_total, score_fit, score_safety, score_evidence, score_value, why_it_fits, evidence_used, avoid_flags_triggered)
          VALUES (:run,:rank,:pid,:total,:fit,:safety,:evidence,:value,:why,:evidence_used,:avoid)
        """), {"run": str(run_id), "rank": idx, "pid": p["id"], "total": total, "fit": fit, "safety": safety,
                 "evidence": evidence, "value": value, "why": why, "evidence_used": citations, "avoid": triggered})
        cards.append(RecommendationCard(
            rank=idx, product_id=p["id"], name=p["name"], brand=p["brand"], category=p["category"],
            price=float(p["price"] or 0), size_ml=float(p["size_ml"] or 0), cost_per_ml=float(p["cost_per_ml"] or 0),
            key_actives=p.get("ingredients_normalized") or [], avoid_flags=triggered,
            evidence_strength=strength, citations=citations, why_it_fits=why,
            links={"amazon": p["amazon_url"], "ewg": p["ewg_url"], "yuka": p["yuka_url"]},
            scores={"total": total, "fit": fit, "safety": safety, "evidence": evidence, "value": value},
        ))
    db.commit()
    return RecommendationsResponse(recommendation_run_id=run_id, items=cards)


@app.get("/products")
def list_products(status: str | None = None, category: str | None = None, db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    query = """
      SELECT p.id, p.name, p.brand, p.price, p.size_ml, p.cost_per_ml, p.status, c.code AS category
      FROM product p JOIN product_category c ON c.id=p.category_id WHERE 1=1
    """
    params = {}
    if status:
        query += " AND p.status=:status"
        params["status"] = status
    if category:
        query += " AND c.code=:category"
        params["category"] = category
    return db.execute(text(query), params).mappings().all()


@app.post("/products/import_csv")
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    content = file.file.read().decode()
    reader = csv.DictReader(StringIO(content))
    inserted = 0
    for row in reader:
        category_id = db.execute(text("SELECT id FROM product_category WHERE code=:c"), {"c": row["category"]}).scalar()
        if not category_id:
            continue
        size_ml = float(row.get("size_ml") or 0)
        price = float(row.get("price") or 0)
        cost_per_ml = round(price / size_ml, 6) if size_ml else None
        db.execute(text("""
          INSERT INTO product (id, name, brand, category_id, ingredients_normalized, price, size_value, size_unit, size_ml, cost_per_ml, amazon_url, ewg_url, yuka_url, flags, status)
          VALUES (:id,:name,:brand,:category_id,:ingredients,:price,:size_value,:size_unit,:size_ml,:cost,:amazon,:ewg,:yuka,:flags,:status)
        """), {"id": str(uuid4()), "name": row["name"], "brand": row["brand"], "category_id": category_id,
                 "ingredients": [a.strip() for a in row.get("actives", "").split("|") if a.strip()], "price": price,
                 "size_value": size_ml, "size_unit": "mL", "size_ml": size_ml, "cost": cost_per_ml,
                 "amazon": row.get("amazon_url"), "ewg": row.get("ewg_url"), "yuka": row.get("yuka_url"),
                 "flags": {}, "status": row.get("status", "pending_review")})
        inserted += 1
    db.commit()
    return {"inserted": inserted}


@app.patch("/products/{product_id}")
def patch_product(product_id: str, payload: ProductPatch, db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    fields = payload.model_dump(exclude_none=True)
    if "price" in fields and ("size_ml" in fields or "size_value" in fields):
        size_ml = fields.get("size_ml") or fields.get("size_value")
        fields["cost_per_ml"] = round(fields["price"] / size_ml, 6) if size_ml else None
    for k, v in fields.items():
        db.execute(text(f"UPDATE product SET {k}=:{k} WHERE id=:id"), {k: v, "id": product_id})
    db.commit()
    return {"updated": True}


@app.get("/admin/weights")
def get_weights(db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    return db.execute(text("SELECT code, name, weight_0_10 FROM feature_weight ORDER BY code")).mappings().all()


@app.patch("/admin/weights/{code}")
def patch_weight(code: str, payload: WeightUpdate, db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    db.execute(text("UPDATE feature_weight SET weight_0_10=:w, updated_at=now() WHERE code=:code"), {"w": payload.weight_0_10, "code": code})
    db.commit()
    return {"updated": True}


@app.get("/admin/flag_rules")
def get_flag_rules(db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    return db.execute(text("SELECT code, name, rule_json FROM flag_rule ORDER BY code")).mappings().all()


@app.patch("/admin/flag_rules/{code}")
def patch_flag_rule(code: str, payload: FlagRuleUpdate, db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    db.execute(text("UPDATE flag_rule SET rule_json=:r, updated_at=now() WHERE code=:code"), {"r": payload.rule_json, "code": code})
    db.commit()
    return {"updated": True}


@app.get("/admin/evidence_snippets")
def list_evidence(db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    return db.execute(text("SELECT id, summary, strength, citations FROM evidence_snippet ORDER BY created_at DESC LIMIT 200")).mappings().all()


@app.post("/admin/evidence_snippets")
def create_evidence(payload: EvidenceSnippetCreate, db: Session = Depends(get_db), _: None = Depends(admin_auth)):
    provider_id = db.execute(text("SELECT id FROM evidence_provider WHERE code=:c"), {"c": payload.provider_code}).scalar()
    active_id = db.execute(text("SELECT id FROM active_ingredient WHERE code=:c"), {"c": payload.active_code}).scalar()
    diagnosis_id = db.execute(text("SELECT id FROM diagnosis WHERE code=:c"), {"c": payload.diagnosis_code}).scalar()
    if not all([provider_id, active_id, diagnosis_id]):
        raise HTTPException(status_code=400, detail="Unknown provider/active/diagnosis code")
    db.execute(text("""
      INSERT INTO evidence_snippet (id, provider_id, active_ingredient_id, diagnosis_id, summary, strength, citations)
      VALUES (:id,:provider,:active,:diagnosis,:summary,:strength,:citations)
    """), {"id": str(uuid4()), "provider": provider_id, "active": active_id, "diagnosis": diagnosis_id,
             "summary": payload.summary, "strength": payload.strength, "citations": payload.citations})
    db.commit()
    return {"created": True}
