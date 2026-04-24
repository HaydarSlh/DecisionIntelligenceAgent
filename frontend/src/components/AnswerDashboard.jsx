import AnswerCard from './AnswerCard.jsx'
import SourcePanel from './SourcePanel.jsx'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

function SimilarityBars({ tickets }) {
  if (!tickets?.length) return null
  return (
    <div className="sim-section">
      <h3 className="sim-title">
        <span style={{ color: 'var(--teal-text)' }}>▸</span>
        Chunk similarity scores
      </h3>
      {tickets.map((t, i) => {
        const sim = t.distance != null ? 1 - t.distance : 0
        const brand = t.brand || t.source || '—'
        return (
          <div key={i} className="sim-row">
            <span className="sim-rank">{i + 1}</span>
            <span className="sim-brand">{brand}</span>
            <div className="sim-track">
              <div className="sim-fill" style={{ width: `${sim * 100}%` }} />
            </div>
            <span className="sim-val">{sim.toFixed(3)}</span>
          </div>
        )
      })}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.fill }}>
          {p.name}: <strong>{p.value} ms</strong>
        </p>
      ))}
    </div>
  )
}

export default function AnswerDashboard({ rag, plain }) {
  const latencyData = [
    { name: 'RAG',    value: rag?.latency_ms   ?? 0, fill: '#7c6eff' },
    { name: 'Direct', value: plain?.latency_ms  ?? 0, fill: '#00e5b0' },
  ]

  const fourWayRows = [
    {
      system: 'RAG Answer', tag: 'rag',
      answer: rag?.answer?.slice(0, 80) + (rag?.answer?.length > 80 ? '…' : ''),
      sources: rag?.retrieved_tickets?.length ?? 0,
      latency: rag?.latency_ms,
      cost: rag?.cost_usd,
      accuracy: '—',
    },
    {
      system: 'Direct LLM', tag: 'plain',
      answer: plain?.answer?.slice(0, 80) + (plain?.answer?.length > 80 ? '…' : ''),
      sources: 0,
      latency: plain?.latency_ms,
      cost: plain?.cost_usd,
      accuracy: '—',
    },
  ]

  return (
    <div className="answer-dashboard">
      <div className="answers-grid">
        {/* Left: RAG answer + visual sources */}
        <div className="rag-column">
          <AnswerCard
            title="RAG Answer"
            type="rag"
            icon="🔍"
            answer={rag?.answer}
            latency={rag?.latency_ms}
            model={rag?.model}
          />
          <SimilarityBars tickets={rag?.retrieved_tickets} />
          <SourcePanel tickets={rag?.retrieved_tickets} />
        </div>

        {/* Right: Direct LLM */}
        <AnswerCard
          title="Direct LLM Answer"
          type="plain"
          icon="💬"
          answer={plain?.answer}
          latency={plain?.latency_ms}
          model={plain?.model}
        />
      </div>

      {/* Latency chart */}
      <div className="charts-grid single">
        <div className="chart-card">
          <h3 className="chart-title">Response Latency Comparison</h3>
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={latencyData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}ms`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,.04)' }} />
              <Bar dataKey="value" name="Latency" radius={[6, 6, 0, 0]} maxBarSize={70}>
                {latencyData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Four-way comparison */}
      <div className="fourway-section">
        <h2 className="section-heading">
          <span className="section-icon purple">📊</span>
          Answer Comparison
        </h2>
        <div className="table-wrapper">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>System</th>
                <th>Sources used</th>
                <th>Latency</th>
                <th>Cost / call</th>
                <th>Grounding</th>
              </tr>
            </thead>
            <tbody>
              {fourWayRows.map(r => (
                <tr key={r.tag} className={`row-${r.tag}`}>
                  <td className="col-system">
                    {r.system} <span className={`system-tag tag-${r.tag}`}>{r.tag}</span>
                  </td>
                  <td>
                    {r.sources > 0
                      ? <span className="count-badge">{r.sources} chunks</span>
                      : <span style={{ color: 'var(--text-dim)' }}>None</span>
                    }
                  </td>
                  <td className="col-latency">{r.latency != null ? `${r.latency} ms` : '—'}</td>
                  <td className="col-cost">{r.cost != null ? `$${r.cost.toFixed(6)}` : '—'}</td>
                  <td>
                    {r.tag === 'rag'
                      ? <span style={{ color: 'var(--normal)', fontWeight: 600 }}>✓ Grounded</span>
                      : <span style={{ color: 'var(--text-dim)' }}>General knowledge</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="recommendation-box">
          <div className="rec-title">💡 When to use each</div>
          <p>
            <strong>RAG Answer</strong> should be preferred for customer support: it retrieves real
            past resolutions from your Twitter dataset, cites them explicitly, and refuses to
            guess when no similar thread is found.
          </p>
          <p style={{ marginTop: '.6rem' }}>
            <strong>Direct LLM</strong> answers from training data — useful as a fallback when the
            vector store has no similar threads, or for general product questions not covered by
            past support conversations. Watch for hallucination on specific policy or pricing details.
          </p>
        </div>
      </div>
    </div>
  )
}
