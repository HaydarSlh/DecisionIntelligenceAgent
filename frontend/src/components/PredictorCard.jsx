import ConfidenceGauge from './ConfidenceGauge.jsx'

const VARIANTS = {
  ml:  { title: 'ML Classifier',  icon: '⚡', tag: 'ml',  tagClass: 'tag-ml'  },
  llm: { title: 'LLM Zero-shot',  icon: '🤖', tag: 'llm', tagClass: 'tag-llm' },
}

export default function PredictorCard({ type, data }) {
  const v = VARIANTS[type]
  const confidence = data?.confidence != null ? data.confidence * 100 : 0
  const isUrgent = data?.label === 'urgent'

  return (
    <div className={`predictor-card predictor-card-${type}`}>
      <div className="predictor-header">
        <span className="predictor-icon">{v.icon}</span>
        <div className="predictor-title-group">
          <span className="predictor-title">{v.title}</span>
          <span className={`system-tag ${v.tagClass}`}>{v.tag}</span>
        </div>
        {data?.label && (
          <span className={`priority-pill priority-${data.label}`}>
            {isUrgent ? '🔴' : '🟢'}&nbsp;{data.label.toUpperCase()}
          </span>
        )}
      </div>

      <ConfidenceGauge confidence={confidence} label={data?.label} id={type} />

      {data?.explanation && (
        <p className="predictor-explanation">{data.explanation}</p>
      )}

      <div className="predictor-metrics">
        <div className="pred-metric">
          <span className="pred-metric-label">Latency</span>
          <span className="pred-metric-value">
            {data?.latency_ms != null ? `${data.latency_ms} ms` : '—'}
          </span>
        </div>
        <div className="pred-metric-divider" />
        <div className="pred-metric">
          <span className="pred-metric-label">Cost / call</span>
          <span className="pred-metric-value">
            {type === 'ml'
              ? <span className="free-badge">~$0</span>
              : data?.cost_usd != null
                ? `$${data.cost_usd.toFixed(6)}`
                : '—'}
          </span>
        </div>
        {type === 'ml' && data?.model_available === false && (
          <div className="pred-metric">
            <span className="pred-metric-warn">Model not loaded</span>
          </div>
        )}
      </div>
    </div>
  )
}
