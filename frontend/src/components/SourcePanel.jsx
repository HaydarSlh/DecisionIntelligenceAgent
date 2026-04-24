import { useState } from 'react'

function ThreadCard({ ticket, index }) {
  const [open, setOpen] = useState(false)
  const similarity = ticket.distance != null ? (1 - ticket.distance).toFixed(3) : '—'
  const brand = ticket.brand || ticket.source || '—'

  return (
    <div className="thread-card">
      <button
        className="thread-header"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <span className="thread-rank">{index + 1}</span>
        <span className="thread-brand">{brand}</span>
        <span className="thread-sim-badge">sim {similarity}</span>
        {ticket.thread_id && (
          <span className="thread-id">#{ticket.thread_id}</span>
        )}
        <span className={`thread-chevron${open ? ' open' : ''}`}>▼</span>
      </button>
      {open && (
        <pre className="thread-body">{ticket.text}</pre>
      )}
    </div>
  )
}

export default function SourcePanel({ tickets }) {
  if (!tickets || tickets.length === 0) {
    return (
      <section className="source-panel empty">
        <h2 className="section-heading">
          <span className="section-icon teal">📂</span>
          Sources
        </h2>
        <p className="empty-msg">No conversations retrieved — ingest threads first via <code>/ingest/threads</code>.</p>
      </section>
    )
  }

  return (
    <section className="source-panel">
      <h2 className="section-heading">
        <span className="section-icon teal">📂</span>
        Sources used for this answer
        <span className="count-badge">{tickets.length}</span>
      </h2>
      <div className="thread-list">
        {tickets.map((t, i) => (
          <ThreadCard key={t.thread_id || t.source || i} ticket={t} index={i} />
        ))}
      </div>
    </section>
  )
}
