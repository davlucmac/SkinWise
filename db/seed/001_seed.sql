INSERT INTO product_category (code, name)
VALUES
  ('cleanser','Cleanser'),('moisturizer','Moisturizer'),('sunscreen','Sunscreen'),('retinoid','Retinoid'),
  ('vitamin_c','Vitamin C / Antioxidant'),('azelaic','Azelaic Acid'),('niacinamide','Niacinamide / Barrier'),
  ('exfoliant','Exfoliant (AHA/BHA/PHA)'),('pigment_corrector','Pigment Corrector'),('acne_treatment','Acne Treatment')
ON CONFLICT (code) DO NOTHING;

INSERT INTO diagnosis (code, name)
VALUES
  ('acne','Acne'),('rosacea','Rosacea'),('melasma_pih','Melasma / PIH'),('eczema_atopic','Eczema / Atopic'),
  ('seb_derm','Seborrheic Dermatitis'),('perioral_dermatitis','Perioral Dermatitis')
ON CONFLICT (code) DO NOTHING;

INSERT INTO ingredient_avoid_rule (code, name, description)
VALUES
  ('fragrance','Fragrance','Fragrance and parfum components'),
  ('essential_oils','Essential Oils','Includes volatile fragrant oils'),
  ('mi_mci','MI/MCI','Methylisothiazolinone and methylchloroisothiazolinone'),
  ('denat_alcohol','Denatured Alcohol','Potentially irritating alcohols')
ON CONFLICT (code) DO NOTHING;

INSERT INTO evidence_provider (code, name)
VALUES
  ('europe_pmc','Europe PMC'),('openalex','OpenAlex'),('semantic_scholar','Semantic Scholar'),('clinicaltrials','ClinicalTrials.gov'),('pubmed','PubMed')
ON CONFLICT (code) DO NOTHING;

INSERT INTO active_ingredient (code, name)
VALUES
  ('retinol','Retinol'),('azelaic_acid','Azelaic Acid'),('niacinamide','Niacinamide'),('vitamin_c','Vitamin C'),
  ('salicylic_acid','Salicylic Acid'),('benzoyl_peroxide','Benzoyl Peroxide'),('ceramide','Ceramide'),('zinc_oxide','Zinc Oxide')
ON CONFLICT (code) DO NOTHING;

INSERT INTO feature_weight (code, name, weight_0_10)
VALUES
  ('skin_diagnoses','Skin Diagnoses',10),('skin_type','Skin Type',9),('acne_level_type','Acne Level + Type',9),
  ('melasma_level','Melasma Level',9),('rosacea_level','Rosacea Level',9),('sensitivities','Sensitivities',9),
  ('fitzpatrick_type','Fitzpatrick Type',8),('photodamage','Photodamage',8),('sun_exposure','Sun Exposure',8),
  ('age','Age',7),('wrinkles','Wrinkles',7),('skin_laxity','Skin Laxity',6),('client_concern','Client Concern',5),
  ('sex','Sex',4),('screen_exposure','Screen Exposure',3),('nationality_biology','Nationality Biology',0),('nationality_availability','Nationality Availability',5)
ON CONFLICT (code) DO UPDATE SET weight_0_10 = EXCLUDED.weight_0_10;

INSERT INTO fitzpatrick_modifier (fitzpatrick_type, rules_json)
VALUES
  (1, '{"spf_priority":1.25,"irritation_penalty":1.2,"retinoid_penalty":1.15}'::jsonb),
  (2, '{"spf_priority":1.2,"irritation_penalty":1.15,"retinoid_penalty":1.1}'::jsonb),
  (3, '{"spf_priority":1.1,"pigment_prevention":1.1}'::jsonb),
  (4, '{"spf_priority":1.1,"pigment_prevention":1.15}'::jsonb),
  (5, '{"iron_oxide_boost":1.25,"pih_safe_boost":1.25,"irritation_penalty":1.15}'::jsonb),
  (6, '{"iron_oxide_boost":1.3,"pih_safe_boost":1.3,"irritation_penalty":1.2}'::jsonb)
ON CONFLICT (fitzpatrick_type) DO UPDATE SET rules_json = EXCLUDED.rules_json;

INSERT INTO flag_rule (code, name, rule_json)
VALUES
('fragrance','Fragrance', '{"match_any":["fragrance","parfum"],"severity":"high"}'::jsonb),
('essential_oils','Essential Oils', '{"match_any":["lavender oil","tea tree oil"],"severity":"medium"}'::jsonb),
('mi_mci','MI/MCI', '{"match_any":["methylisothiazolinone","methylchloroisothiazolinone"],"severity":"high"}'::jsonb),
('denat_alcohol','Denatured Alcohol', '{"match_any":["alcohol denat"],"severity":"medium"}'::jsonb)
ON CONFLICT (code) DO UPDATE SET rule_json = EXCLUDED.rule_json;

INSERT INTO product (name, brand, category_id, ingredients_normalized, price, size_value, size_unit, size_ml, multipack_count, cost_per_ml, amazon_url, ewg_url, yuka_url, flags, status)
SELECT
  'SkinWise Product ' || gs,
  'Brand ' || ((gs % 12) + 1),
  pc.id,
  CASE WHEN pc.code IN ('sunscreen','moisturizer')
    THEN '["niacinamide","ceramide","zinc oxide"]'::jsonb
    ELSE '["niacinamide","salicylic acid"]'::jsonb
  END,
  (10 + (gs % 30))::numeric(10,2),
  50,
  'mL',
  50,
  1,
  ((10 + (gs % 30)) / 50.0)::numeric(10,6),
  'https://amazon.com/dp/SKINWISE' || gs,
  'https://ewg.org/skindeep/product/' || gs,
  'https://yuka.io/en/product/' || gs,
  CASE WHEN gs % 4 = 0 THEN '{"fragrance": true}'::jsonb ELSE '{}'::jsonb END,
  'active'::product_status
FROM generate_series(1,60) AS gs
JOIN LATERAL (
  SELECT id, code FROM product_category ORDER BY code OFFSET (gs - 1) % 10 LIMIT 1
) pc ON TRUE
ON CONFLICT DO NOTHING;

INSERT INTO evidence_snippet (provider_id, active_ingredient_id, diagnosis_id, summary, strength, citations)
SELECT ep.id, ai.id, d.id,
  ai.name || ' has supportive evidence for ' || d.name || ' in topical skincare use.',
  CASE WHEN d.code IN ('acne','rosacea') THEN 'A'::evidence_strength WHEN d.code = 'melasma_pih' THEN 'B'::evidence_strength ELSE 'C'::evidence_strength END,
  jsonb_build_array(jsonb_build_object('title','MVP stub citation','url','https://example.org/' || ai.code || '-' || d.code))
FROM active_ingredient ai
CROSS JOIN diagnosis d
JOIN evidence_provider ep ON ep.code = 'openalex'
ON CONFLICT DO NOTHING;
