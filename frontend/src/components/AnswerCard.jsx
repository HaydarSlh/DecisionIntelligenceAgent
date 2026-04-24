export default function AnswerCard({ title, type, icon, answer, latency, model }) {
  return (
    <div className={`answer-card answer-card-${type}`}>
      <div className="answer-card-header">
        <div className={`answer-card-icon icon-${type}`}>{icon}</div>
        <span className="answer-card-title">{title}</span>
        <span className={`badge badge-${type}`}>{type === 'rag' ? 'RAG' : 'Direct'}</span>
      </div>
      <div className="answer-body">
        <p className="answer-text">{answer}</p>
        <div className="answer-meta">
          <span className="meta-chip">⏱ {latency} ms</span>
          {model && <span className="meta-chip model-chip">✦ {model}</span>}
        </div>
      </div>
    </div>
  )
}
