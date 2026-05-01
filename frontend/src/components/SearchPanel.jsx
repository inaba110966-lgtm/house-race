import { useState } from 'react'

export default function SearchPanel() {
  const [query, setQuery] = useState('')
  const [collection, setCollection] = useState('races')
  const [topK, setTopK] = useState(5)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, collection, top_k: topK }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'APIエラー')
      }
      const data = await res.json()
      setResults(data.results)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="panel-title">セマンティック検索</h1>
      <p className="panel-desc">
        自然言語でJRA-VANデータを検索します。キーワードに意味的に近いレースや馬を返します。
      </p>

      <div className="search-controls">
        <input
          className="search-input"
          placeholder="例: 芝の長距離で安定したサンデー系の馬"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') search() }}
        />
        <select
          className="select-input"
          value={collection}
          onChange={e => setCollection(e.target.value)}
        >
          <option value="races">レース</option>
          <option value="horses">馬</option>
        </select>
        <input
          className="option-input"
          type="number"
          min={1}
          max={20}
          value={topK}
          onChange={e => setTopK(Number(e.target.value))}
          style={{ width: 64 }}
        />
        <button className="search-btn" onClick={search} disabled={loading || !query.trim()}>
          {loading ? '検索中...' : '検索'}
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div className="search-results">
        {results.map((r, i) => (
          <div key={i} className="search-result-card">
            <div className="search-result-header">
              <span className="search-result-title">
                {r.payload?.race_name || r.payload?.horse_name || `結果 ${i + 1}`}
              </span>
              <span className="score-badge">類似度 {(r.score * 100).toFixed(1)}%</span>
            </div>
            <div className="search-result-text">
              {r.payload?.race_date && `📅 ${r.payload.race_date}`}
              {r.payload?.venue_name && ` | 🏟 ${r.payload.venue_name}`}
              {r.payload?.surface && ` | ${r.payload.surface}${r.payload.distance}m`}
              {r.payload?.grade && ` | ${r.payload.grade}`}
              {'\n'}
              {r.payload?.text ? r.payload.text.slice(0, 300) + (r.payload.text.length > 300 ? '…' : '') : ''}
            </div>
          </div>
        ))}
        {results.length === 0 && !loading && query && (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 32 }}>
            検索結果がありません
          </p>
        )}
      </div>
    </div>
  )
}
