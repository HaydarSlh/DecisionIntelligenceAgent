import PredictorCard from './PredictorCard.jsx'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts'

function HorizBar({ label, value, max, color, display }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="hbar-row">
      <span className="hbar-label">{label}</span>
      <div className="hbar-track">
        <div
          className="hbar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="hbar-value">{display}</span>
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
          {p.name}: <strong>{p.value}{p.name === 'Confidence' ? '%' : p.name === 'Latency' ? ' ms' : ''}</strong>
        </p>
      ))}
    </div>
  )
}

export default function PriorityDashboard({ ml, llm, mlMetrics }) {
  const mlConf   = ml?.confidence  != null ? +(ml.confidence  * 100).toFixed(1) : 0
  const llmConf  = llm?.confidence != null ? +(llm.confidence * 100).toFixed(1) : 0
  const mlLat    = ml?.latency_ms  ?? 0
  const llmLat   = llm?.latency_ms ?? 0
  const mlCost   = 0
  const llmCost  = llm?.cost_usd   ?? 0
  const mlAcc    = mlMetrics?.accuracy != null ? +(mlMetrics.accuracy * 100).toFixed(1) : null

  const agree = ml?.label && llm?.label && ml.label === llm.label

  const confidenceData = [
    { name: 'ML Classifier',  value: mlConf,  fill: '#22d98a' },
    { name: 'LLM Zero-shot',  value: llmConf, fill: '#f59e0b' },
  ]

  const latencyData = [
    { name: 'ML Classifier',  value: mlLat,  fill: '#22d98a' },
    { name: 'LLM Zero-shot',  value: llmLat, fill: '#f59e0b' },
  ]

  const fourWayData = [
    {
      name: 'ML Classifier',
      Confidence: mlConf,
      'Latency (ms)': mlLat,
      'Cost (μ$)': +(mlCost * 1_000_000).toFixed(0),
      'Test Accuracy': mlAcc ?? 0,
    },
    {
      name: 'LLM Zero-shot',
      Confidence: llmConf,
      'Latency (ms)': llmLat,
      'Cost (μ$)': +(llmCost * 1_000_000).toFixed(2),
      'Test Accuracy': 0,
    },
  ]

  return (
    <div className="priority-dashboard">
      {/* Agreement banner */}
      {ml?.label && llm?.label && (
        <div className={`agreement-banner ${agree ? 'agree' : 'disagree'}`}>
          <span className="agreement-icon">{agree ? '✓' : '⚠'}</span>
          {agree
            ? `Both models agree: this ticket is ${ml.label.toUpperCase()}`
            : `Models disagree — ML predicts ${ml.label?.toUpperCase()}, LLM predicts ${llm?.label?.toUpperCase()}`
          }
        </div>
      )}

      {/* Two predictor cards */}
      <div className="predictors-grid">
        <PredictorCard type="ml"  data={ml}  />
        <PredictorCard type="llm" data={llm} />
      </div>

      {/* Charts section */}
      <div className="charts-grid">
        {/* Confidence bar chart */}
        <div className="chart-card">
          <h3 className="chart-title">Confidence Score</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={confidenceData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,.04)' }} />
              <Bar dataKey="value" name="Confidence" radius={[6, 6, 0, 0]} maxBarSize={60}>
                {confidenceData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Latency bar chart */}
        <div className="chart-card">
          <h3 className="chart-title">Response Latency</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={latencyData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}ms`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,.04)' }} />
              <Bar dataKey="value" name="Latency" radius={[6, 6, 0, 0]} maxBarSize={60}>
                {latencyData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Four-way comparison table */}
      <div className="fourway-section">
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
                <th>Confidence</th>
                <th>Test Accuracy</th>
                <th>Latency</th>
                <th>Cost / call</th>
              </tr>
            </thead>
            <tbody>
              <tr className="row-ml">
                <td className="col-system">ML Classifier <span className="system-tag tag-ml">ml</span></td>
                <td><span className={`priority-badge priority-${ml?.label}`}>{ml?.label?.toUpperCase() ?? '—'}</span></td>
                <td className="col-accuracy">{mlConf > 0 ? `${mlConf}%` : '—'}</td>
                <td className="col-accuracy">{mlAcc != null ? `${mlAcc}%` : '—'}</td>
                <td className="col-latency">{mlLat > 0 ? `${mlLat} ms` : '—'}</td>
                <td><span className="free-badge">~$0</span></td>
              </tr>
              <tr className="row-llm">
                <td className="col-system">LLM Zero-shot <span className="system-tag tag-llm">llm</span></td>
                <td><span className={`priority-badge priority-${llm?.label}`}>{llm?.label?.toUpperCase() ?? '—'}</span></td>
                <td className="col-accuracy">{llmConf > 0 ? `${llmConf}%` : '—'}</td>
                <td className="col-accuracy">—</td>
                <td className="col-latency">{llmLat > 0 ? `${llmLat} ms` : '—'}</td>
                <td className="col-cost">{llmCost > 0 ? `$${llmCost.toFixed(6)}` : '—'}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Production recommendation */}
        <div className="recommendation-box">
          <div className="rec-title">💡 Production Recommendation</div>
          <p>
            <strong>Deploy the ML Classifier</strong> for high-volume triage.
            It runs in ~{mlLat} ms at effectively <strong>$0</strong> per call
            {mlAcc != null ? ` with ${mlAcc}% test accuracy` : ''} — making it
            suitable for processing thousands of tickets per second with no API cost.
          </p>
          <p style={{ marginTop: '.6rem' }}>
            Reserve the <strong>LLM Zero-shot</strong> ({llmLat} ms,{' '}
            {llmCost > 0 ? `$${llmCost.toFixed(4)}/call` : 'API cost'}) as a
            second-pass verifier on cases where the ML model returns low
            confidence (under 60%), or for novel ticket types not well represented
            in the training data.
          </p>
          <p style={{ marginTop: '.6rem' }}>
            At 10,000 tickets/hour: ML costs <strong>~$0</strong> vs LLM at{' '}
            <strong>~${(llmCost * 10000).toFixed(2)}/hr</strong>. The hybrid
            approach — ML first, LLM only on edge cases — cuts cost by {'>'} 90%
            while maintaining quality on ambiguous tickets.
          </p>
        </div>
      </div>
    </div>
  )
}
