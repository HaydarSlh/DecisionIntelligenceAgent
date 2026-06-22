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

  const [ragResult, plainResult, mlResult, llmResult] = await Promise.allSettled([
    post(`/ask/rag${brandParam}`, body),
    post('/ask', body),
    post('/priority/ml', body),
    post('/priority/llm', body),
  ])

  const unwrap = (r) => r.status === 'fulfilled' ? r.value : null
  const errors = [ragResult, plainResult, mlResult, llmResult]
    .filter(r => r.status === 'rejected')
    .map(r => r.reason?.message)

  if (errors.length === 4) throw new Error(errors[0])

  return {
    rag: unwrap(ragResult),
    plain: unwrap(plainResult),
    ml: unwrap(mlResult),
    llm: unwrap(llmResult),
    errors,
  }
}

export async function fetchMetrics() {
  return get('/store/metrics')
}
