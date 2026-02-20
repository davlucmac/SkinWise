from app.services.scoring import _value_percentiles, _fit_score, IntakeCtx


def test_value_percentile_bounds():
    products = [
        {"id": "1", "category": "sunscreen", "cost_per_ml": 1.0},
        {"id": "2", "category": "sunscreen", "cost_per_ml": 2.0},
    ]
    scores = _value_percentiles(products)
    assert 0 <= scores["1"] <= 10
    assert 0 <= scores["2"] <= 10
    assert scores["1"] > scores["2"]


def test_fitzpatrick_i_boosts_spf():
    intake = IntakeCtx(id="x", fitzpatrick_type=1, photodamage=1, melasma_level=0, rosacea_level=0, acne_level=0, sun_exposure_level=1, budget_max_price=None, budget_max_cost_per_ml=None)
    w = {"photodamage": 8}
    spf = _fit_score({"category": "sunscreen", "ingredients_normalized": []}, intake, w)
    exfol = _fit_score({"category": "exfoliant", "ingredients_normalized": []}, intake, w)
    assert spf > exfol
