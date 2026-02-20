'use client'

import { useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function Home() {
  const [step, setStep] = useState(1)
  const [intakeId, setIntakeId] = useState('')
  const [mode, setMode] = useState<'overall'|'category'>('overall')
  const [categoryCode, setCategoryCode] = useState('sunscreen')
  const [results, setResults] = useState<any[]>([])
  const [form, setForm] = useState<any>({
    age: 30, sex: 'female', fitzpatrick_type: 3, locale: 'en-US', skin_type: 'combination',
    diagnosis_codes: ['acne'], avoid_codes: ['fragrance'], photodamage: 1, melasma_level: 0,
    rosacea_level: 0, acne_level: 2, wrinkles_level: 1, laxity_level: 0, sun_exposure_level: 2,
    screen_exposure_level: 2, acne_type: 'mixed', budget_max_price: 35, budget_max_cost_per_ml: 1.2,
    primary_concern_text: 'breakouts and dark marks', skin_problems_text: 'oiliness and clogged pores'
  })

  async function submitIntake() {
    const res = await fetch(`${API}/intake`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(form) })
    const data = await res.json()
    setIntakeId(data.intake_profile_id)
    setStep(3)
  }

  async function getRecommendations() {
    const res = await fetch(`${API}/recommendations`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ intake_profile_id: intakeId, mode, category_code: mode === 'category' ? categoryCode : null }) })
    const data = await res.json()
    setResults(data.items || [])
  }

  return <div className="container">
    <h1>SkinWise Intake</h1>
    {step === 1 && <div className="card">
      <h3>Step 1 — Demographics & biology</h3>
      <div className="grid">
        <label>Age<input type="number" value={form.age} onChange={e=>setForm({...form, age:Number(e.target.value)})} /></label>
        <label>Sex<select value={form.sex} onChange={e=>setForm({...form, sex:e.target.value})}><option>female</option><option>male</option><option>other</option></select></label>
        <label>Fitzpatrick<select value={form.fitzpatrick_type} onChange={e=>setForm({...form, fitzpatrick_type:Number(e.target.value)})}>{[1,2,3,4,5,6].map(v=><option key={v} value={v}>{v}</option>)}</select></label>
        <label>Skin Type<select value={form.skin_type} onChange={e=>setForm({...form, skin_type:e.target.value})}><option>dry</option><option>oily</option><option>combination</option><option>normal</option><option>sensitive</option></select></label>
      </div>
      <button onClick={()=>setStep(2)}>Next</button>
    </div>}

    {step === 2 && <div className="card">
      <h3>Step 2 — Severity, avoid, budget</h3>
      <div className="grid">
        {['photodamage','melasma_level','rosacea_level','acne_level','wrinkles_level','laxity_level','sun_exposure_level','screen_exposure_level'].map((k)=><label key={k}>{k}<input type="range" min={0} max={4} value={form[k]} onChange={e=>setForm({...form, [k]: Number(e.target.value)})}/><span>{form[k]}</span></label>)}
        <label>Diagnoses (comma)<input value={form.diagnosis_codes.join(',')} onChange={e=>setForm({...form, diagnosis_codes:e.target.value.split(',').map((s)=>s.trim()).filter(Boolean)})}/></label>
        <label>Avoid Toggles (comma)<input value={form.avoid_codes.join(',')} onChange={e=>setForm({...form, avoid_codes:e.target.value.split(',').map((s)=>s.trim()).filter(Boolean)})}/></label>
        <label>Budget max price<input type="number" value={form.budget_max_price} onChange={e=>setForm({...form, budget_max_price:Number(e.target.value)})}/></label>
        <label>Budget max $/mL<input type="number" step="0.01" value={form.budget_max_cost_per_ml} onChange={e=>setForm({...form, budget_max_cost_per_ml:Number(e.target.value)})}/></label>
      </div>
      <button onClick={submitIntake}>Save Intake</button>
    </div>}

    {step === 3 && <div className="card">
      <h3>Step 3 — Recommendation Mode</h3>
      <p className='small'>Intake ID: {intakeId}</p>
      <label>Mode<select value={mode} onChange={e=>setMode(e.target.value as any)}><option value='overall'>overall</option><option value='category'>category</option></select></label>
      {mode === 'category' && <label>Category code<input value={categoryCode} onChange={e=>setCategoryCode(e.target.value)} /></label>}
      <button onClick={getRecommendations}>Get exactly 5 recommendations</button>
    </div>}

    {results.map((r)=> <div key={r.product_id} className="card">
      <h3>#{r.rank} {r.name} <span className='small'>({r.category})</span></h3>
      <p>{r.brand} • ${r.price} • {r.size_ml} mL • ${r.cost_per_ml}/mL</p>
      <p><b>Key actives:</b> {(r.key_actives || []).join(', ')}</p>
      <p><b>Avoid flags:</b> {(r.avoid_flags || []).join(', ') || 'None'}</p>
      <p><b>Evidence:</b> {r.evidence_strength}</p>
      <p><b>Why it fits:</b> {r.why_it_fits}</p>
      <p><a href={r.links?.amazon}>Amazon</a> | <a href={r.links?.ewg}>EWG</a> | <a href={r.links?.yuka}>Yuka</a></p>
    </div>)}
  </div>
}
