'use client'
import { useEffect, useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function AdminPage() {
  const [weights, setWeights] = useState<any[]>([])
  const [products, setProducts] = useState<any[]>([])
  const auth = 'Basic ' + btoa('admin:admin')

  async function load() {
    const w = await fetch(`${API}/admin/weights`, {headers:{Authorization:auth}}).then(r=>r.json())
    const p = await fetch(`${API}/products?status=pending_review`, {headers:{Authorization:auth}}).then(r=>r.json())
    setWeights(w); setProducts(p)
  }
  useEffect(()=>{ load() },[])

  async function updateWeight(code:string, weight:number) {
    await fetch(`${API}/admin/weights/${code}`, {method:'PATCH', headers:{'Content-Type':'application/json', Authorization:auth}, body: JSON.stringify({weight_0_10:weight})})
    load()
  }

  return <div className='container'>
    <h1>Admin</h1>
    <div className='card'>
      <h3>Feature Weights</h3>
      {weights.map((w)=><div key={w.code} style={{display:'flex',gap:8,marginBottom:8}}>
        <span style={{minWidth:220}}>{w.name}</span>
        <input type='number' min={0} max={10} defaultValue={w.weight_0_10} onBlur={e=>updateWeight(w.code, Number(e.target.value))}/>
      </div>)}
    </div>
    <div className='card'>
      <h3>Pending Products</h3>
      {products.map((p)=><div key={p.id}>{p.name} ({p.category})</div>)}
    </div>
  </div>
}
