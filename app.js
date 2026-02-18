const OPTIONS = {
  diagnoses: ["acne", "rosacea", "melasma/PIH", "eczema", "seb derm"],
  problems: ["dryness", "redness", "dark spots", "texture", "oiliness", "dullness"],
  sensitivities: ["fragrance", "essential oils", "MI/MCI", "alcohol denat", "high-acid exfoliants"]
};

const DEFAULT_WEIGHTS = {
  skinDiagnoses: 10,
  skinType: 9,
  acne: 9,
  melasma: 9,
  rosacea: 9,
  sensitivities: 9,
  fitzpatrick: 8,
  photodamage: 8,
  sunExposure: 8,
  age: 7,
  wrinkles: 7,
  skinLaxity: 6,
  clientProblem: 5,
  sex: 4,
  screenExposure: 3,
  nationalityAvailability: 5
};

const EVIDENCE = {
  strong: 1,
  moderate: 0.75,
  limited: 0.5
};

const PRODUCTS = [
  { name: "Mineral Tint SPF 50", category: "sunscreen", price: 29, sizeMl: 50, actives: ["zinc oxide", "iron oxides"], avoids: ["fragrance", "essential oils"], irritancy: 1, pihSafe: true, evidence: { melasma: "strong", photodamage: "strong", rosacea: "moderate" }, citations: ["AAD sunscreen guidance", "Melasma visible-light studies"] },
  { name: "Azelaic 10 Serum", category: "treatment", price: 18, sizeMl: 30, actives: ["azelaic acid 10%", "niacinamide"], avoids: ["fragrance"], irritancy: 2, pihSafe: true, evidence: { acne: "moderate", rosacea: "moderate", melasma: "moderate" }, citations: ["Cochrane acne review", "Rosacea guideline"] },
  { name: "Retinal Night Emulsion", category: "retinoid", price: 34, sizeMl: 30, actives: ["retinaldehyde", "ceramides"], avoids: ["fragrance", "essential oils"], irritancy: 3, pihSafe: true, evidence: { acne: "strong", wrinkles: "strong", photodamage: "moderate" }, citations: ["AAD acne guideline", "Photoaging retinoid meta-analysis"] },
  { name: "Barrier Cream", category: "moisturizer", price: 22, sizeMl: 75, actives: ["ceramides", "cholesterol", "glycerin"], avoids: ["fragrance", "essential oils", "MI/MCI"], irritancy: 1, pihSafe: true, evidence: { eczema: "moderate", rosacea: "limited", skinType: "strong" }, citations: ["Barrier repair literature"] },
  { name: "BHA 2% Gel", category: "exfoliant", price: 20, sizeMl: 40, actives: ["salicylic acid 2%"], avoids: ["fragrance"], irritancy: 4, pihSafe: false, evidence: { acne: "strong", oiliness: "moderate" }, citations: ["Acne topical keratolytic evidence"] },
  { name: "BPO 2.5% Cleanser", category: "cleanser", price: 14, sizeMl: 120, actives: ["benzoyl peroxide 2.5%"], avoids: ["fragrance"], irritancy: 3, pihSafe: false, evidence: { acne: "strong" }, citations: ["AAD acne treatment pathway"] },
  { name: "Pigment Control Serum", category: "treatment", price: 36, sizeMl: 30, actives: ["tranexamic acid", "niacinamide", "licorice"], avoids: ["fragrance", "essential oils"], irritancy: 2, pihSafe: true, evidence: { melasma: "moderate", pih: "moderate" }, citations: ["PIH treatment consensus"] },
  { name: "Peptide Firming Lotion", category: "moisturizer", price: 30, sizeMl: 60, actives: ["peptides", "hyaluronic acid"], avoids: ["fragrance"], irritancy: 1, pihSafe: true, evidence: { wrinkles: "limited", laxity: "limited" }, citations: ["Peptide topical studies"] }
];

const fitzMap = {
  always_burn_never_tan: "I",
  burn_then_tan_light: "II",
  sometimes_burn_gradual_tan: "III",
  rarely_burn_tan_well: "IV",
  almost_never_burn_deep_tan: "V",
  never_burn_deeply_pigmented: "VI"
};

function createChips(containerId, values) {
  const container = document.getElementById(containerId);
  values.forEach((value) => {
    const label = document.createElement("label");
    label.className = "chip";
    label.innerHTML = `<input type="checkbox" value="${value}"> ${value}`;
    label.querySelector("input").addEventListener("change", () => {
      label.classList.toggle("active", label.querySelector("input").checked);
    });
    container.appendChild(label);
  });
}

function createWeightEditor() {
  const container = document.getElementById("weights");
  Object.entries(DEFAULT_WEIGHTS).forEach(([key, val]) => {
    const label = document.createElement("label");
    label.innerHTML = `${key}<input type="number" min="0" max="10" step="1" data-weight="${key}" value="${val}">`;
    container.appendChild(label);
  });
}

function selectedFrom(containerId) {
  return [...document.querySelectorAll(`#${containerId} input:checked`)].map((x) => x.value);
}

function getWeight(key) {
  const node = document.querySelector(`[data-weight="${key}"]`);
  return Number(node?.value ?? DEFAULT_WEIGHTS[key]);
}

function collectForm() {
  let fitz = document.getElementById("fitzpatrick").value;
  if (!fitz) {
    fitz = fitzMap[document.getElementById("fitz-helper").value] || "III";
  }
  return {
    age: Number(document.getElementById("age").value),
    sex: document.getElementById("sex").value,
    fitzpatrick: fitz,
    skinType: document.getElementById("skin-type").value,
    diagnoses: selectedFrom("diagnoses"),
    problems: selectedFrom("problems"),
    sensitivities: selectedFrom("sensitivities"),
    photodamage: Number(document.getElementById("photodamage").value),
    melasma: Number(document.getElementById("melasma").value),
    rosacea: Number(document.getElementById("rosacea").value),
    sun: Number(document.getElementById("sun").value),
    screen: Number(document.getElementById("screen").value),
    acne: Number(document.getElementById("acne").value),
    acneType: document.getElementById("acne-type").value,
    laxity: Number(document.getElementById("laxity").value),
    wrinkles: Number(document.getElementById("wrinkles").value),
    locale: document.getElementById("locale").value,
    clientProblem: document.getElementById("client-problem").value.toLowerCase(),
    budgetPrice: Number(document.getElementById("budget-price").value || Infinity),
    budgetUnit: Number(document.getElementById("budget-unit").value || Infinity)
  };
}

function fitzModifier(fitz, product, intake) {
  let bonus = 0;
  if (["I", "II"].includes(fitz)) {
    if (product.category === "sunscreen") bonus += 0.25;
    if (product.category === "exfoliant") bonus -= 0.2;
    if (product.category === "retinoid") bonus -= 0.15;
  } else if (["III", "IV"].includes(fitz)) {
    if (product.category === "sunscreen") bonus += 0.15;
    if (intake.melasma > 0 && product.pihSafe) bonus += 0.1;
  } else {
    if (product.actives.includes("iron oxides")) bonus += 0.3;
    if (product.pihSafe) bonus += 0.15;
    if (product.irritancy >= 3 && intake.acne < 3) bonus -= 0.25;
  }
  return bonus;
}

function scoreProduct(p, intake) {
  const unitPrice = p.price / p.sizeMl;
  const inBudget = p.price <= intake.budgetPrice && unitPrice <= intake.budgetUnit;

  const w = (key) => getWeight(key) / 10;

  let fitRaw = 0;
  if (intake.diagnoses.some((d) => p.evidence[d] || (d === "melasma/PIH" && (p.evidence.melasma || p.evidence.pih)))) fitRaw += 10 * w("skinDiagnoses");
  if (intake.skinType === "sensitive" && p.irritancy <= 2) fitRaw += 7 * w("skinType");
  if (intake.acne > 0 && p.evidence.acne) fitRaw += (5 + intake.acne) * w("acne");
  fitRaw += intake.melasma * (p.evidence.melasma ? 1.6 : 0.2) * w("melasma");
  fitRaw += intake.rosacea * (p.evidence.rosacea ? 1.4 : 0.2) * w("rosacea");
  fitRaw += intake.photodamage * (p.evidence.photodamage ? 1.2 : 0.2) * w("photodamage");
  fitRaw += intake.sun * (p.category === "sunscreen" ? 1.1 : 0.1) * w("sunExposure");
  fitRaw += intake.wrinkles * (p.evidence.wrinkles ? 1.3 : 0.2) * w("wrinkles");
  fitRaw += intake.laxity * (p.evidence.laxity ? 1.2 : 0.3) * w("skinLaxity");
  fitRaw += fitzModifier(intake.fitzpatrick, p, intake) * 10 * w("fitzpatrick");
  if (intake.clientProblem.includes("dark") && (p.evidence.melasma || p.evidence.pih)) fitRaw += 3 * w("clientProblem");

  const fitScore = Math.max(0, Math.min(45, fitRaw));

  let safetyRaw = 25;
  intake.sensitivities.forEach((s) => {
    if (!p.avoids.includes(s)) safetyRaw -= 8;
  });
  if (intake.skinType === "sensitive" && p.irritancy >= 3) safetyRaw -= 6;
  const safetyScore = Math.max(0, Math.min(25, safetyRaw));

  let evidenceRaw = 0;
  Object.entries(p.evidence).forEach(([condition, strength]) => {
    const relevance = intake.diagnoses.includes(condition) || (condition === "acne" && intake.acne > 0) || (condition === "melasma" && intake.melasma > 0) || (condition === "rosacea" && intake.rosacea > 0) || (condition === "wrinkles" && intake.wrinkles > 0) || (condition === "laxity" && intake.laxity > 0) || condition === "photodamage";
    if (relevance) evidenceRaw += 6 * EVIDENCE[strength];
  });
  const evidenceScore = Math.max(0, Math.min(20, evidenceRaw));

  let valueScore = 10 - Math.min(10, unitPrice * 8);
  if (!inBudget) valueScore -= 2;
  valueScore = Math.max(0, Math.min(10, valueScore));

  const composite = Math.round(fitScore + safetyScore + evidenceScore + valueScore);
  return { ...p, unitPrice, fitScore, safetyScore, evidenceScore, valueScore, composite, inBudget };
}

function renderResults(scored, intake) {
  const container = document.getElementById("results");
  container.innerHTML = "";

  scored.slice(0, 5).forEach((p, idx) => {
    const avoidFlags = intake.sensitivities.filter((s) => !p.avoids.includes(s));
    const why = [
      p.category === "sunscreen" && intake.sun > 1 ? "high sun exposure support" : null,
      p.evidence.acne && intake.acne > 0 ? "acne-targeted active match" : null,
      (p.evidence.melasma || p.evidence.pih) && intake.melasma > 0 ? "pigment-safe support" : null,
      intake.skinType === "sensitive" && p.irritancy <= 2 ? "sensitive-skin compatible" : null,
      p.inBudget ? "within budget targets" : "slightly above budget"
    ].filter(Boolean).join(", ");

    const node = document.createElement("article");
    node.className = "result";
    node.innerHTML = `
      <h3>${idx + 1}. ${p.name} <span class="score">(${p.composite}/100)</span></h3>
      <p class="meta">Price: $${p.price} • Size: ${p.sizeMl}mL • $/mL: $${p.unitPrice.toFixed(2)}</p>
      <p><small class="tag">Fit ${p.fitScore.toFixed(1)}/45</small><small class="tag">Safety ${p.safetyScore.toFixed(1)}/25</small><small class="tag">Evidence ${p.evidenceScore.toFixed(1)}/20</small><small class="tag">Value ${p.valueScore.toFixed(1)}/10</small></p>
      <p><strong>Key actives:</strong> ${p.actives.join(", ")}</p>
      <p><strong>Avoid flags:</strong> ${avoidFlags.length ? avoidFlags.join(", ") : "None"}</p>
      <p><strong>Evidence strength + citations:</strong> ${Object.entries(p.evidence).map(([k,v]) => `${k}: ${v}`).join("; ")} (${p.citations.join(" | ")})</p>
      <p><strong>Why it fits:</strong> ${why}</p>
    `;
    container.appendChild(node);
  });
}

function initRangeOutputs() {
  ["photodamage", "melasma", "rosacea", "sun", "screen", "acne", "laxity", "wrinkles"].forEach((id) => {
    const input = document.getElementById(id);
    const out = document.getElementById(`${id}-o`);
    input.addEventListener("input", () => out.textContent = input.value);
  });
}

createChips("diagnoses", OPTIONS.diagnoses);
createChips("problems", OPTIONS.problems);
createChips("sensitivities", OPTIONS.sensitivities);
createWeightEditor();
initRangeOutputs();

document.getElementById("intake-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const intake = collectForm();
  const scored = PRODUCTS.map((p) => scoreProduct(p, intake)).sort((a, b) => b.composite - a.composite);
  renderResults(scored, intake);
});
