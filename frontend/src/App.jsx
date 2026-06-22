import { useState, useEffect } from 'react'
import QueryForm from './components/QueryForm.jsx'
import ModeNav from './components/ModeNav.jsx'
import AnswerDashboard from './components/AnswerDashboard.jsx'
import PriorityDashboard from './components/PriorityDashboard.jsx'
import { runQuery, fetchMetrics } from './api.js'

function LoadingState({ mode }) {
  const labels = mode === 'answer'
    ? ['RAG Answer', 'Direct LLM Answer']
    : ['ML Classifier', 'LLM Zero-shot']
  return (
    <div className="loading-grid">
      {labels.map(label => (
        <div key={label} className="skeleton-card">
          <div className="skeleton-title" />
          <div className="skeleton-line" />
          <div className="skeleton-line" />
          <div className="skeleton-line short" />
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [mode, setMode] = useState('answer')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [mlMetrics, setMlMetrics] = useState(null)

  useEffect(() => {
    fetchMetrics().then(setMlMetrics).catch(() => {})
  }, [])

  async function handleSubmit(text, brand) {
    setLoading(true)
    setError(null)
    try {
      const data = await runQuery(text, brand)
      setResults(data)
      setError(data.errors?.length ? `Some predictions failed: ${data.errors.join(' | ')}` : null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-logo">🧠</div>
          <div className="header-content">
            <h1 className="header-title">Decision Intelligence Assistant</h1>
            <p className="header-sub">Powered by RAG · ML · LLM Zero-shot</p>
          </div>
          <div className="header-pills">
            <span className="tech-pill purple">Gemini 2.5 Flash</span>
            <span className="tech-pill teal">ChromaDB</span>
            <span className="tech-pill">LightGBM</span>
            <a href="/logs" className="tech-pill logs-link" target="_blank" rel="noreferrer">📋 Logs</a>
          </div>
        </div>
      </header>

      <main className="app-main">
        <ModeNav mode={mode} onChange={mode => { setMode(mode); setResults(null) }} />

        <QueryForm onSubmit={handleSubmit} loading={loading} mode={mode} />

        {error && (
          <div className={`error-banner ${results ? 'error-banner--warn' : ''}`}>
            <span>⚠</span> <strong>{results ? 'Warning' : 'Error'}:</strong>&ensp;{error}
          </div>
        )}

        {loading && <LoadingState mode={mode} />}

        {results && !loading && (
          mode === 'answer'
            ? <AnswerDashboard rag={results.rag} plain={results.plain} />
            : <PriorityDashboard ml={results.ml} llm={results.llm} mlMetrics={mlMetrics} />
        )}
      </main>

      <footer className="app-footer">
        Customer Support on Twitter (twcs) · Gemini 2.5 Flash · LightGBM · ChromaDB
      </footer>
    </div>
  )
}
