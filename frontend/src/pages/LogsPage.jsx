import { useState, useEffect, useCallback } from 'react'

const EVENT_COLORS = {
  ask_rag:      { color: '#a89fff', bg: 'rgba(124,110,255,.13)', label: 'RAG' },
  ask_plain:    { color: '#4dffd4', bg: 'rgba(0,229,176,.11)',   label: 'Direct' },
  priority_ml:  { color: '#22d98a', bg: 'rgba(34,217,138,.1)',   label: 'ML' },
  priority_llm: { color: '#f59e0b', bg: 'rgba(245,158,11,.1)',   label: 'LLM' },
}

function EventBadge({ event }) {
  const cfg = EVENT_COLORS[event] ?? { color: '#8a94b0', bg: 'rgba(138,148,176,.1)', label: event }
  return (
    <span className="log-event-badge" style={{ color: cfg.color, background: cfg.bg }}>
      {cfg.label}
    </span>
  )
}

function PriorityDot({ label }) {
  if (!label) return null
  const color = label === 'urgent' ? '#ff5757' : '#22d98a'
  return <span className="log-priority-dot" style={{ background: color }} title={label} />
}

function LogRow({ entry, idx }) {
  const [open, setOpen] = useState(false)
  const ts = new Date(entry.timestamp)
  const timeStr = ts.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const dateStr = ts.toLocaleDateString([], { month: 'short', day: 'numeric' })

  const query = entry.query || entry.text || '—'
  const latency = entry.latency_ms
  const cost = entry.cost_usd
  const label = entry.label
  const retrieved = entry.retrieved_count

  return (
    <div className={`log-row ${open ? 'open' : ''}`}>
      <button className="log-row-header" onClick={() => setOpen(o => !o)}>
        <span className="log-idx">#{idx + 1}</span>
        <EventBadge event={entry.event} />
        <PriorityDot label={label} />
        <span className="log-query">{query.length > 80 ? query.slice(0, 80) + '…' : query}</span>
        <span className="log-meta-chips">
          {latency != null && <span className="log-chip">⏱ {latency} ms</span>}
          {retrieved != null && <span className="log-chip">📂 {retrieved} chunks</span>}
          {cost != null && <span className="log-chip">💰 ${cost.toFixed(6)}</span>}
          {label && <span className="log-chip" style={{ color: label === 'urgent' ? '#ff5757' : '#22d98a' }}>{label}</span>}
        </span>
        <span className="log-time">{dateStr} {timeStr}</span>
        <span className={`log-chevron${open ? ' open' : ''}`}>▼</span>
      </button>
      {open && (
        <div className="log-detail">
          <pre className="log-json">{JSON.stringify(entry, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={{ color }}>{value}</div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export default function LogsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/store/logs?limit=200')
      setData(await res.json())
    } catch {
      setData({ entries: [], total: 0 })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const entries = data?.entries ?? []

  // Stats
  const ragCount   = entries.filter(e => e.event === 'ask_rag').length
  const plainCount = entries.filter(e => e.event === 'ask_plain').length
  const mlCount    = entries.filter(e => e.event === 'priority_ml').length
  const urgentCount= entries.filter(e => e.label === 'urgent').length

  const avgLatency = entries.length
    ? (entries.reduce((s, e) => s + (e.latency_ms ?? 0), 0) / entries.length).toFixed(0)
    : '—'
  const totalCost = entries.reduce((s, e) => s + (e.cost_usd ?? 0), 0)

  const filtered = entries.filter(e => {
    if (filter !== 'all' && e.event !== filter) return false
    if (search && !(e.query || e.text || '').toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="logs-page">
      <div className="logs-header">
        <a href="/" className="logs-back">← Back to app</a>
        <h1 className="logs-title">Query Logs</h1>
        <p className="logs-sub">Live view of queries, retrievals, and model outputs</p>
        <button className="logs-refresh" onClick={load} disabled={loading}>
          {loading ? <span className="spinner" /> : '↻'} Refresh
        </button>
      </div>

      {/* Stats row */}
      <div className="stats-grid">
        <StatCard label="Total entries" value={data?.total ?? '—'} color="var(--accent-text)" />
        <StatCard label="RAG queries" value={ragCount} color="#a89fff" />
        <StatCard label="Direct LLM" value={plainCount} color="#4dffd4" />
        <StatCard label="ML priority" value={mlCount} color="#22d98a" />
        <StatCard label="Urgent tickets" value={urgentCount} sub="predicted" color="#ff5757" />
        <StatCard label="Avg latency" value={avgLatency !== '—' ? `${avgLatency} ms` : '—'} color="var(--text-muted)" />
        <StatCard label="Total API cost" value={`$${totalCost.toFixed(4)}`} color="#f59e0b" />
      </div>

      {/* Filter row */}
      <div className="logs-controls">
        <div className="filter-pills">
          {['all', 'ask_rag', 'ask_plain', 'priority_ml', 'priority_llm'].map(f => (
            <button
              key={f}
              className={`filter-pill ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : EVENT_COLORS[f]?.label ?? f}
            </button>
          ))}
        </div>
        <input
          className="log-search"
          placeholder="Search queries…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Log entries */}
      <div className="log-list">
        {loading && <div className="log-empty">Loading…</div>}
        {!loading && filtered.length === 0 && (
          <div className="log-empty">
            No entries yet — run a query in the main app first.
          </div>
        )}
        {filtered.map((entry, i) => (
          <LogRow key={i} entry={entry} idx={i} />
        ))}
      </div>
    </div>
  )
}
