import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const EXAMPLES = [
  '東京芝2400mの重賞で過去好走している血統パターンを教えて',
  '阪神外回りのG1で騎乗回数が多く好成績の騎手は？',
  '馬場が稍重から重になった時に成績が上がる馬の傾向は？',
  '函館競馬場の芝1200mでよく勝つ調教師と馬の特徴は？',
  '上がり3F最速馬が着外になりやすいレース条件を分析して',
]

export default function AnalysisPanel() {
  const [query, setQuery] = useState('')
  const [raceId, setRaceId] = useState('')
  const [topK, setTopK] = useState(10)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showSources, setShowSources] = useState(false)

  const submit = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/v1/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, race_id: raceId || null, top_k: topK }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'APIエラー')
      }
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="panel-title">AI競馬分析</h1>
      <p className="panel-desc">
        JRA-VANの過去データをVector DBで検索し、Claudeが根拠ある分析を生成します。
      </p>

      <div className="example-queries">
        {EXAMPLES.map(ex => (
          <button key={ex} className="example-btn" onClick={() => setQuery(ex)}>
            {ex}
          </button>
        ))}
      </div>

      <div className="query-box">
        <div className="query-row">
          <textarea
            className="query-input"
            placeholder="分析したい内容を入力してください（例: 京都記念出走馬の過去成績と適性分析）"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) submit() }}
          />
          <button className="submit-btn" onClick={submit} disabled={loading || !query.trim()}>
            {loading ? '分析中...' : '分析する'}
          </button>
        </div>
        <div className="options-row">
          <span className="option-label">レースID (任意):</span>
          <input
            className="option-input"
            placeholder="例: 2024050501"
            value={raceId}
            onChange={e => setRaceId(e.target.value)}
          />
          <span className="option-label">参照データ数:</span>
          <input
            className="option-input"
            type="number"
            min={1}
            max={30}
            value={topK}
            onChange={e => setTopK(Number(e.target.value))}
          />
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <span>JRA-VANデータを検索してClaudeが分析中...</span>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {result && (
        <div className="result-card">
          <div className="result-label">AI分析結果</div>
          <div className="analysis-text">
            <ReactMarkdown>{result.analysis}</ReactMarkdown>
          </div>

          {result.sources?.length > 0 && (
            <div className="sources">
              <button className="sources-toggle" onClick={() => setShowSources(s => !s)}>
                {showSources ? '参照データを隠す' : `参照データを表示 (${result.sources.length}件)`}
              </button>
              {showSources && (
                <div className="sources-list">
                  {result.sources.map((s, i) => (
                    <div key={i} className="source-item">
                      {s.race_name || s.horse_name || s.race_id || `データ ${i + 1}`}
                      {s.race_date && ` — ${s.race_date}`}
                      {s.venue_name && ` @ ${s.venue_name}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
