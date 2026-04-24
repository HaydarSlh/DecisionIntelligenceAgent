function fmt(val, prefix = '', suffix = '') {
  if (val == null) return '—'
  return `${prefix}${val}${suffix}`
}

function PriorityBadge({ label }) {
  if (!label) return <span style={{ color: 'var(--text-dim)' }}>—</span>
  return <span className={`priority-badge priority-${label}`}>{label.toUpperCase()}</span>
}

function Row({ rowClass, system, tag, label, confidence, accuracy, latency, cost, note }) {
  return (
    <tr className={rowClass}>
      <td className="col-system">
        {system}
        {tag && <span className={`system-tag tag-${tag}`}>{tag}</span>}
      </td>
      <td className="col-label">
        <PriorityBadge label={label} />
        {confidence != null && (
          <span className="conf-score">{(confidence * 100).toFixed(0)}%</span>
        )}
      </td>
      <td className="col-accuracy">{accuracy}</td>
      <td className="col-latency">{fmt(latency, '', ' ms')}</td>
      <td className="col-cost">
        {cost != null
          ? cost === 0
            ? <span className="free-tag">~$0</span>
            : `$${cost.toFixed(6)}`
          : '—'}
        {note && <span className="cost-note"> {note}</span>}
      </td>
    </tr>
  )
}

export default function ComparisonTable({ results, mlMetrics }) {
  const { rag, plain, ml, llm } = results
  const mlAccuracy = mlMetrics?.accuracy
    ? `${(mlMetrics.accuracy * 100).toFixed(1)}%`
    : '—'

  return (
    <section className="comparison-section">
      <h2 className="section-heading">
        <span className="section-icon purple">📊</span>
        Four-Way Comparison
      </h2>
      <div className="table-wrapper">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>System</th>
              <th>Priority</th>
              <th>Test Accuracy</th>
              <th>Latency</th>
              <th>Cost / call</th>
            </tr>
          </thead>
          <tbody>
            <Row
              rowClass="row-rag"
              system="RAG Answer"
              tag="rag"
              label={null}
              accuracy="—"
              latency={rag?.latency_ms}
              cost={rag?.cost_usd ?? null}
            />
            <Row
              rowClass="row-plain"
              system="Non-RAG Answer"
              tag="plain"
              label={null}
              accuracy="—"
              latency={plain?.latency_ms}
              cost={plain?.cost_usd ?? null}
            />
            <Row
              rowClass="row-ml"
              system="ML Classifier"
              tag="ml"
              label={ml?.label}
              confidence={ml?.confidence}
              accuracy={mlAccuracy}
              latency={ml?.latency_ms}
              cost={0}
              note="(trained)"
            />
            <Row
              rowClass="row-llm"
              system="LLM Zero-shot"
              tag="llm"
              label={llm?.label}
              confidence={llm?.confidence}
              accuracy="—"
              latency={llm?.latency_ms}
              cost={llm?.cost_usd ?? null}
            />
          </tbody>
        </table>
      </div>

      {llm?.explanation && (
        <div className="llm-explanation">
          <span className="explanation-label">LLM reasoning:</span>
          {llm.explanation}
        </div>
      )}

      <div className="recommendation-box">
        <strong>At 10,000 tickets/hour:</strong> The ML classifier runs in ~{ml?.latency_ms ?? '?'} ms
        at effectively $0, vs the LLM at ~{llm?.latency_ms ?? '?'} ms and{' '}
        ${llm?.cost_usd?.toFixed(6) ?? '?'}/call (~${llm?.cost_usd != null ? (llm.cost_usd * 10000).toFixed(2) : '?'}/hr).
        Use the ML model for high-volume triage; escalate to the LLM for borderline cases.
      </div>
    </section>
  )
}
