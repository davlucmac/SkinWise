CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$ BEGIN
  CREATE TYPE product_status AS ENUM ('pending_review', 'active', 'excluded');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE evidence_strength AS ENUM ('A', 'B', 'C');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE sex_type AS ENUM ('female', 'male', 'intersex', 'other', 'prefer_not_say');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE skin_type AS ENUM ('dry', 'oily', 'combination', 'normal', 'sensitive');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE acne_type AS ENUM ('comedonal', 'inflammatory', 'mixed', 'cystic');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS app_user (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS intake_profile (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES app_user(id) ON DELETE SET NULL,
  age INTEGER CHECK (age IS NULL OR (age >= 0 AND age <= 130)),
  sex sex_type,
  fitzpatrick_type SMALLINT CHECK (fitzpatrick_type IS NULL OR (fitzpatrick_type BETWEEN 1 AND 6)),
  locale TEXT,
  skin_type skin_type,
  skin_problems_text TEXT,
  primary_concern_text TEXT,
  photodamage SMALLINT NOT NULL DEFAULT 0 CHECK (photodamage BETWEEN 0 AND 4),
  melasma_level SMALLINT NOT NULL DEFAULT 0 CHECK (melasma_level BETWEEN 0 AND 4),
  rosacea_level SMALLINT NOT NULL DEFAULT 0 CHECK (rosacea_level BETWEEN 0 AND 4),
  acne_level SMALLINT NOT NULL DEFAULT 0 CHECK (acne_level BETWEEN 0 AND 4),
  wrinkles_level SMALLINT NOT NULL DEFAULT 0 CHECK (wrinkles_level BETWEEN 0 AND 4),
  laxity_level SMALLINT NOT NULL DEFAULT 0 CHECK (laxity_level BETWEEN 0 AND 4),
  sun_exposure_level SMALLINT NOT NULL DEFAULT 0 CHECK (sun_exposure_level BETWEEN 0 AND 4),
  screen_exposure_level SMALLINT NOT NULL DEFAULT 0 CHECK (screen_exposure_level BETWEEN 0 AND 4),
  acne_type acne_type,
  pregnant_or_bf BOOLEAN,
  budget_max_price NUMERIC(10,2),
  budget_max_cost_per_ml NUMERIC(10,4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS diagnosis (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intake_profile_diagnosis (
  intake_profile_id UUID NOT NULL REFERENCES intake_profile(id) ON DELETE CASCADE,
  diagnosis_id UUID NOT NULL REFERENCES diagnosis(id) ON DELETE RESTRICT,
  PRIMARY KEY (intake_profile_id, diagnosis_id)
);

CREATE TABLE IF NOT EXISTS ingredient_avoid_rule (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS intake_profile_avoid (
  intake_profile_id UUID NOT NULL REFERENCES intake_profile(id) ON DELETE CASCADE,
  ingredient_avoid_rule_id UUID NOT NULL REFERENCES ingredient_avoid_rule(id) ON DELETE RESTRICT,
  PRIMARY KEY (intake_profile_id, ingredient_avoid_rule_id)
);

CREATE TABLE IF NOT EXISTS product_category (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  brand TEXT NOT NULL,
  category_id UUID REFERENCES product_category(id) ON DELETE RESTRICT,
  inci_raw TEXT,
  ingredients_normalized JSONB,
  price NUMERIC(10,2),
  size_value NUMERIC(10,3),
  size_unit TEXT,
  size_ml NUMERIC(10,3),
  multipack_count INTEGER DEFAULT 1 CHECK (multipack_count >= 1),
  cost_per_ml NUMERIC(10,6),
  amazon_url TEXT,
  ewg_url TEXT,
  yuka_url TEXT,
  flags JSONB,
  status product_status NOT NULL DEFAULT 'pending_review',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_status ON product(status);
CREATE INDEX IF NOT EXISTS idx_product_category ON product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_cost_per_ml ON product(cost_per_ml);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_product_updated_at ON product;
CREATE TRIGGER trg_product_updated_at
BEFORE UPDATE ON product
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS active_ingredient (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS product_active_ingredient (
  product_id UUID NOT NULL REFERENCES product(id) ON DELETE CASCADE,
  active_ingredient_id UUID NOT NULL REFERENCES active_ingredient(id) ON DELETE RESTRICT,
  concentration_text TEXT,
  PRIMARY KEY (product_id, active_ingredient_id)
);

CREATE TABLE IF NOT EXISTS evidence_provider (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_snippet (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  provider_id UUID REFERENCES evidence_provider(id) ON DELETE SET NULL,
  active_ingredient_id UUID NOT NULL REFERENCES active_ingredient(id) ON DELETE RESTRICT,
  diagnosis_id UUID NOT NULL REFERENCES diagnosis(id) ON DELETE RESTRICT,
  summary TEXT NOT NULL,
  strength evidence_strength NOT NULL,
  citations JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_active_diag ON evidence_snippet(active_ingredient_id, diagnosis_id);

CREATE TABLE IF NOT EXISTS feature_weight (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  weight_0_10 SMALLINT NOT NULL CHECK (weight_0_10 BETWEEN 0 AND 10),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fitzpatrick_modifier (
  fitzpatrick_type SMALLINT PRIMARY KEY CHECK (fitzpatrick_type BETWEEN 1 AND 6),
  rules_json JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS flag_rule (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  rule_json JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_run (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  intake_profile_id UUID NOT NULL REFERENCES intake_profile(id) ON DELETE CASCADE,
  mode TEXT NOT NULL DEFAULT 'overall',
  requested_category_id UUID REFERENCES product_category(id) ON DELETE SET NULL,
  weights_snapshot JSONB,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_item (
  recommendation_run_id UUID NOT NULL REFERENCES recommendation_run(id) ON DELETE CASCADE,
  rank SMALLINT NOT NULL CHECK (rank BETWEEN 1 AND 5),
  product_id UUID NOT NULL REFERENCES product(id) ON DELETE RESTRICT,
  score_total NUMERIC(6,2) NOT NULL,
  score_fit NUMERIC(6,2) NOT NULL,
  score_safety NUMERIC(6,2) NOT NULL,
  score_evidence NUMERIC(6,2) NOT NULL,
  score_value NUMERIC(6,2) NOT NULL,
  why_it_fits TEXT,
  evidence_used JSONB,
  avoid_flags_triggered JSONB,
  PRIMARY KEY (recommendation_run_id, rank)
);

CREATE INDEX IF NOT EXISTS idx_reco_item_product ON recommendation_item(product_id);
