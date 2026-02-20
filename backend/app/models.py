from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, Numeric, SmallInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class IntakeProfile(Base):
    __tablename__ = "intake_profile"
    id = Column(UUID(as_uuid=True), primary_key=True)
    age = Column(Integer)
    sex = Column(String)
    fitzpatrick_type = Column(SmallInteger)
    locale = Column(Text)
    skin_type = Column(String)
    skin_problems_text = Column(Text)
    primary_concern_text = Column(Text)
    photodamage = Column(SmallInteger)
    melasma_level = Column(SmallInteger)
    rosacea_level = Column(SmallInteger)
    acne_level = Column(SmallInteger)
    wrinkles_level = Column(SmallInteger)
    laxity_level = Column(SmallInteger)
    sun_exposure_level = Column(SmallInteger)
    screen_exposure_level = Column(SmallInteger)
    acne_type = Column(String)
    pregnant_or_bf = Column(Boolean)
    budget_max_price = Column(Numeric(10,2))
    budget_max_cost_per_ml = Column(Numeric(10,4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProductCategory(Base):
    __tablename__ = "product_category"
    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(Text)
    name = Column(Text)


class Product(Base):
    __tablename__ = "product"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(Text)
    brand = Column(Text)
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_category.id"))
    ingredients_normalized = Column(JSONB)
    price = Column(Numeric(10,2))
    size_value = Column(Numeric(10,3))
    size_unit = Column(Text)
    size_ml = Column(Numeric(10,3))
    cost_per_ml = Column(Numeric(10,6))
    amazon_url = Column(Text)
    ewg_url = Column(Text)
    yuka_url = Column(Text)
    flags = Column(JSONB)
    status = Column(String)


class FeatureWeight(Base):
    __tablename__ = "feature_weight"
    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(Text)
    name = Column(Text)
    weight_0_10 = Column(SmallInteger)


class FlagRule(Base):
    __tablename__ = "flag_rule"
    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(Text)
    name = Column(Text)
    rule_json = Column(JSONB)


class EvidenceSnippet(Base):
    __tablename__ = "evidence_snippet"
    id = Column(UUID(as_uuid=True), primary_key=True)
    summary = Column(Text)
    strength = Column(String)
    citations = Column(JSONB)


class RecommendationRun(Base):
    __tablename__ = "recommendation_run"
    id = Column(UUID(as_uuid=True), primary_key=True)
    intake_profile_id = Column(UUID(as_uuid=True), ForeignKey("intake_profile.id"))
    mode = Column(Text)
    requested_category_id = Column(UUID(as_uuid=True), ForeignKey("product_category.id"))
    weights_snapshot = Column(JSONB)
    notes = Column(Text)


class RecommendationItem(Base):
    __tablename__ = "recommendation_item"
    recommendation_run_id = Column(UUID(as_uuid=True), ForeignKey("recommendation_run.id"), primary_key=True)
    rank = Column(SmallInteger, primary_key=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id"))
    score_total = Column(Numeric(6,2))
    score_fit = Column(Numeric(6,2))
    score_safety = Column(Numeric(6,2))
    score_evidence = Column(Numeric(6,2))
    score_value = Column(Numeric(6,2))
    why_it_fits = Column(Text)
    evidence_used = Column(JSONB)
    avoid_flags_triggered = Column(JSONB)
