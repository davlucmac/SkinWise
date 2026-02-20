from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
try:
    from sqlalchemy import text
except ModuleNotFoundError:
    def text(q):
        return q

EVIDENCE_MULTIPLIER = {"A": 1.0, "B": 0.7, "C": 0.4}


@dataclass
class IntakeCtx:
    id: UUID
    fitzpatrick_type: int | None
    photodamage: int
    melasma_level: int
    rosacea_level: int
    acne_level: int
    sun_exposure_level: int
    budget_max_price: float | None
    budget_max_cost_per_ml: float | None


def _value_percentiles(products: list[dict]) -> dict[str, float]:
    by_cat: dict[str, list[float]] = {}
    for p in products:
        by_cat.setdefault(p["category"], []).append(float(p["cost_per_ml"] or 999))
    result: dict[str, float] = {}
    for p in products:
        costs = sorted(by_cat[p["category"]])
        cost = float(p["cost_per_ml"] or 999)
        rank = costs.index(cost)
        percentile = 1 - (rank / max(len(costs) - 1, 1))
        result[str(p["id"])] = round(percentile * 10, 2)
    return result


def _fit_score(p: dict, intake: IntakeCtx, w: dict[str, int]) -> float:
    base = 10
    if p["category"] == "sunscreen" and (intake.photodamage or intake.melasma_level or intake.rosacea_level or intake.sun_exposure_level):
        base += 8 * (w.get("photodamage", 8) / 10)
    if intake.acne_level > 0 and p["category"] in {"acne_treatment", "retinoid", "azelaic"}:
        base += 8 * (w.get("acne_level_type", 9) / 10)
    if intake.melasma_level > 0 and p["category"] in {"pigment_corrector", "sunscreen", "vitamin_c"}:
        base += 8 * (w.get("melasma_level", 9) / 10)
    if intake.rosacea_level > 0 and p["category"] in {"azelaic", "moisturizer", "sunscreen"}:
        base += 8 * (w.get("rosacea_level", 9) / 10)
    fitz = intake.fitzpatrick_type
    if fitz in (1, 2):
        if p["category"] == "sunscreen":
            base += 4
        if p["category"] in {"retinoid", "exfoliant"}:
            base -= 2
    elif fitz in (5, 6):
        ingredients = p.get("ingredients_normalized") or []
        if "zinc oxide" in [i.lower() for i in ingredients]:
            base += 3
        if p["category"] in {"retinoid", "exfoliant"} and intake.acne_level < 3:
            base -= 2
    return max(0, min(45, round(base, 2)))


def _safety_score(p: dict, avoids: list[str]) -> tuple[float, list[str]]:
    flags = p.get("flags") or {}
    triggered = [k for k in avoids if flags.get(k) is True]
    score = 25 - (len(triggered) * 6)
    return max(0, round(score, 2)), triggered


def _evidence_score(diagnosis_count: int) -> tuple[float, str]:
    if diagnosis_count <= 0:
        return 6.0, "C"
    if diagnosis_count >= 2:
        return 18.0, "A"
    return 13.0, "B"


def compute_recommendations(db, intake_id: UUID, mode: str, category_code: str | None):
    intake_raw = db.execute(text("SELECT * FROM intake_profile WHERE id=:id"), {"id": str(intake_id)}).mappings().first()
    if not intake_raw:
        raise ValueError("Intake profile not found")
    intake = IntakeCtx(
        id=intake_raw["id"], fitzpatrick_type=intake_raw["fitzpatrick_type"], photodamage=intake_raw["photodamage"],
        melasma_level=intake_raw["melasma_level"], rosacea_level=intake_raw["rosacea_level"], acne_level=intake_raw["acne_level"],
        sun_exposure_level=intake_raw["sun_exposure_level"], budget_max_price=float(intake_raw["budget_max_price"] or 0) or None,
        budget_max_cost_per_ml=float(intake_raw["budget_max_cost_per_ml"] or 0) or None,
    )
    avoids = [r[0] for r in db.execute(text("SELECT iar.code FROM ingredient_avoid_rule iar JOIN intake_profile_avoid ipa ON ipa.ingredient_avoid_rule_id=iar.id WHERE ipa.intake_profile_id=:id"), {"id": str(intake_id)}).all()]
    diagnosis_count = db.execute(text("SELECT count(*) FROM intake_profile_diagnosis WHERE intake_profile_id=:id"), {"id": str(intake_id)}).scalar_one()
    weights = {r.code: r.weight_0_10 for r in db.execute(text("SELECT code, weight_0_10 FROM feature_weight")).mappings().all()}

    query = """
    SELECT p.id, p.name, p.brand, p.ingredients_normalized, p.price, p.size_ml, p.cost_per_ml, p.flags,
           p.amazon_url, p.ewg_url, p.yuka_url, c.code AS category
    FROM product p
    JOIN product_category c ON c.id = p.category_id
    WHERE p.status='active'
    """
    params = {}
    if mode == "category" and category_code:
        query += " AND c.code=:cat"
        params["cat"] = category_code
    products = [dict(r) for r in db.execute(text(query), params).mappings().all()]
    if not products:
        raise ValueError("No products available")

    v_scores = _value_percentiles(products)
    scored = []
    for p in products:
        fit = _fit_score(p, intake, weights)
        safety, triggered = _safety_score(p, avoids)
        evidence, strength = _evidence_score(diagnosis_count)
        value = v_scores[str(p["id"])]
        if intake.budget_max_price and p["price"] and float(p["price"]) > intake.budget_max_price:
            value = max(0, value - 5)
        if intake.budget_max_cost_per_ml and p["cost_per_ml"] and float(p["cost_per_ml"]) > intake.budget_max_cost_per_ml:
            value = max(0, value - 3)
        total = round(min(100, fit + safety + evidence + value), 2)
        scored.append((total, fit, safety, evidence, value, strength, triggered, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    chosen = []
    requires_sunscreen = mode == "overall" and any([intake.photodamage > 0, intake.melasma_level > 0, intake.rosacea_level > 0, intake.sun_exposure_level > 0])
    if mode == "overall":
        seen = set()
        for row in scored:
            cat = row[-1]["category"]
            if cat in seen and len(chosen) < 4:
                continue
            chosen.append(row)
            seen.add(cat)
            if len(chosen) == 5:
                break
        if requires_sunscreen and all(r[-1]["category"] != "sunscreen" for r in chosen):
            spf = next((r for r in scored if r[-1]["category"] == "sunscreen"), None)
            if spf:
                chosen[-1] = spf
    else:
        chosen = scored[:5]

    while len(chosen) < 5:
        chosen.append(scored[len(chosen) % len(scored)])

    return chosen[:5], weights
