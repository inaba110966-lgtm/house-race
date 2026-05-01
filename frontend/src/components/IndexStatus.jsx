import { useState, useEffect } from 'react'

export default function IndexStatus() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [indexForm, setIndexForm] = useState({ data_path: '', data_type: 'race' })
  const [indexMsg, setIndexMsg] = useState(null)

  const fetchStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/index/status')
      if (!res.ok) throw new Error('ステータス取得失敗')
      setStatus(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchStatus() }, [])

  const startIndex = async () => {
    setIndexMsg(null)
    try {
      const res = await fetch('/api/v1/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(indexForm),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'エラー')
      setIndexMsg({ type: 'ok', text: data.message })
    } catch (e) {
      setIndexMsg({ type: 'error', text: e.message })
    }
  }

  return (
    <div>
      <h1 className="panel-title">インデックス状況</h1>
      <p className="panel-desc">Qdrant Vector DBのコレクション状況とデータインデックスを管理します。</p>

      <button className="refresh-btn" onClick={fetchStatus} disabled={loading}>
        {loading ? '読込中...' : '更新'}
      </button>

      {error && <div className="error-msg" style={{ marginBottom: 16 }}>{error}</div>}

      {status && (
        <div className="status-grid" style={{ marginBottom: 32 }}>
          {Object.entries(status.collections || {}).map(([name, info]) => (
            <div key={name} className="status-card">
              <div className="status-card-title">
                <span className={`status-dot ${info.status === 'green' ? 'ok' : 'error'}`} />
                {name}
              </div>
              <div className="status-card-value">{(info.points_count || 0).toLocaleString()}</div>
              <div className="status-card-sub">ベクトル数 / ステータス: {info.status}</div>
            </div>
          ))}
        </div>
      )}

      <div className="result-card">
        <div className="result-label">データインデックス</div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
          JRA-VANデータファイルのパスを指定してインデックスを実行します。
          ファイルの種別に応じて自動でQdrantコレクションに格納されます。
        </p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
          <input
            className="search-input"
            placeholder="データパス (例: /data/jra_van/2024)"
            value={indexForm.data_path}
            onChange={e => setIndexForm(f => ({ ...f, data_path: e.target.value }))}
          />
          <select
            className="select-input"
            value={indexForm.data_type}
            onChange={e => setIndexForm(f => ({ ...f, data_type: e.target.value }))}
          >
            <option value="race">レース情報 (RA)</option>
            <option value="result">成績データ (SE)</option>
            <option value="horse">馬情報 (HN)</option>
          </select>
          <button className="submit-btn" onClick={startIndex} disabled={!indexForm.data_path}>
            インデックス開始
          </button>
        </div>
        {indexMsg && (
          <div className={indexMsg.type === 'ok' ? 'result-card' : 'error-msg'} style={{ marginTop: 8 }}>
            {indexMsg.text}
          </div>
        )}
      </div>
    </div>
  )
}
