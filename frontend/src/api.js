const BASE = import.meta.env.VITE_API_URL || ''

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${path} → ${res.status}: ${text}`)
  }
  return res.json()
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

export async function runQuery(text, brand) {
  const body = { text }
  const brandParam = brand ? `?brand=${encodeURIComponent(brand)}` : ''

  const [rag, plain, ml, llm] = await Promise.all([
    post(`/ask/rag${brandParam}`, body),
    post('/ask', body),
    post('/priority/ml', body),
    post('/priority/llm', body),
  ])

  return { rag, plain, ml, llm }
}

export async function fetchMetrics() {
  return get('/store/metrics')
}
