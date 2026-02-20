from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field


class IntakeCreate(BaseModel):
    age: int | None = None
    sex: str | None = None
    fitzpatrick_type: int | None = Field(default=None, ge=1, le=6)
    locale: str | None = None
    skin_type: str | None = None
    diagnosis_codes: list[str] = []
    avoid_codes: list[str] = []
    primary_concern_text: str | None = None
    skin_problems_text: str | None = None
    photodamage: int = Field(default=0, ge=0, le=4)
    melasma_level: int = Field(default=0, ge=0, le=4)
    rosacea_level: int = Field(default=0, ge=0, le=4)
    acne_level: int = Field(default=0, ge=0, le=4)
    wrinkles_level: int = Field(default=0, ge=0, le=4)
    laxity_level: int = Field(default=0, ge=0, le=4)
    sun_exposure_level: int = Field(default=0, ge=0, le=4)
    screen_exposure_level: int = Field(default=0, ge=0, le=4)
    acne_type: str | None = None
    pregnant_or_bf: bool | None = None
    budget_max_price: float | None = None
    budget_max_cost_per_ml: float | None = None


class IntakeResponse(BaseModel):
    intake_profile_id: UUID


class RecoRequest(BaseModel):
    intake_profile_id: UUID
    mode: Literal["overall", "category"] = "overall"
    category_code: str | None = None


class RecommendationCard(BaseModel):
    rank: int
    product_id: UUID
    name: str
    brand: str
    category: str
    price: float | None
    size_ml: float | None
    cost_per_ml: float | None
    key_actives: list[str]
    avoid_flags: list[str]
    evidence_strength: str
    citations: list[dict]
    why_it_fits: str
    links: dict[str, str | None]
    scores: dict[str, float]


class RecommendationsResponse(BaseModel):
    recommendation_run_id: UUID
    items: list[RecommendationCard]


class WeightUpdate(BaseModel):
    weight_0_10: int = Field(ge=0, le=10)


class FlagRuleUpdate(BaseModel):
    rule_json: dict


class ProductPatch(BaseModel):
    price: float | None = None
    size_value: float | None = None
    size_unit: str | None = None
    size_ml: float | None = None
    status: str | None = None


class EvidenceSnippetCreate(BaseModel):
    provider_code: str
    active_code: str
    diagnosis_code: str
    summary: str
    strength: Literal["A", "B", "C"]
    citations: list[dict] = []
