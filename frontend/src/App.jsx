import { useState } from 'react'
import AnalysisPanel from './components/AnalysisPanel'
import SearchPanel from './components/SearchPanel'
import IndexStatus from './components/IndexStatus'
import './styles.css'

const TABS = [
  { id: 'analysis', label: 'AI分析' },
  { id: 'search', label: 'セマンティック検索' },
  { id: 'status', label: 'インデックス状況' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('analysis')

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">🏇</span>
            <span className="logo-text">競馬分析AI</span>
            <span className="logo-badge">JRA-VAN × Vector DB × RAG</span>
          </div>
        </div>
      </header>

      <nav className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {activeTab === 'analysis' && <AnalysisPanel />}
        {activeTab === 'search' && <SearchPanel />}
        {activeTab === 'status' && <IndexStatus />}
      </main>
    </div>
  )
}
