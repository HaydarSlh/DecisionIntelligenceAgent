export default function ModeNav({ mode, onChange }) {
  return (
    <div className="mode-nav">
      <button
        className={`mode-btn ${mode === 'answer' ? 'active' : ''}`}
        onClick={() => onChange('answer')}
      >
        <span className="mode-btn-icon">💬</span>
        <div className="mode-btn-text">
          <span className="mode-btn-label">Customer Support</span>
          <span className="mode-btn-desc">RAG vs Direct LLM answer</span>
        </div>
      </button>
      <button
        className={`mode-btn ${mode === 'priority' ? 'active' : ''}`}
        onClick={() => onChange('priority')}
      >
        <span className="mode-btn-icon">🎯</span>
        <div className="mode-btn-text">
          <span className="mode-btn-label">Priority Predictor</span>
          <span className="mode-btn-desc">ML vs LLM urgency detection</span>
        </div>
      </button>
    </div>
  )
}
