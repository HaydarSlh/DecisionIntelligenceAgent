export default function QueryForm({ onSubmit, loading, mode }) {
  function handleSubmit(e) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    const text = fd.get('text').trim()
    const brand = fd.get('brand')?.trim()
    if (text) onSubmit(text, brand || null)
  }

  const isAnswer = mode === 'answer'

  return (
    <form className="query-form-wrapper" onSubmit={handleSubmit}>
      <label className="query-label" htmlFor="query-text">
        {isAnswer ? 'Customer Support Query' : 'Support Ticket to Classify'}
      </label>
      <textarea
        id="query-text"
        name="text"
        className="query-input"
        placeholder={
          isAnswer
            ? 'Type a customer support question or paste a support ticket…'
            : 'Paste a support ticket to predict its urgency level…'
        }
        rows={3}
        required
      />
      <div className="query-footer">
        {isAnswer && (
          <div className="brand-wrapper">
            <label className="brand-label" htmlFor="brand-filter">Brand filter</label>
            <input
              id="brand-filter"
              name="brand"
              className="brand-input"
              placeholder="e.g. AmazonHelp"
              list="brand-suggestions"
            />
            <datalist id="brand-suggestions">
              {['AmazonHelp', 'AppleSupport', 'Uber_Support', 'SpotifyCares',
                'Delta', 'AmericanAir', 'TMobileHelp', 'comcastcares',
                'XboxSupport', 'hulu_support'].map(b => (
                <option key={b} value={b} />
              ))}
            </datalist>
          </div>
        )}
        <button className="submit-btn" type="submit" disabled={loading}>
          {loading
            ? <><span className="spinner" /> Analyzing…</>
            : isAnswer ? 'Get Answer' : 'Predict Priority'
          }
        </button>
      </div>
    </form>
  )
}
