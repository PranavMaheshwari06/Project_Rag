import { useState } from 'react'
import SearchTab from './SearchTab'
import DashboardTab from './DashboardTab'

type Tab = 'search' | 'dashboard'

export default function App() {
  const [tab, setTab] = useState<Tab>('search')

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>EngineerDoc AI</h1>
          <p className="subtitle">Hybrid retrieval over technical docs — dense + BM25 + RRF + rerank</p>
        </div>
        <nav className="tabs">
          <button className={tab === 'search' ? 'tab active' : 'tab'} onClick={() => setTab('search')}>
            Search
          </button>
          <button className={tab === 'dashboard' ? 'tab active' : 'tab'} onClick={() => setTab('dashboard')}>
            Evaluation Dashboard
          </button>
        </nav>
      </header>
      <main>{tab === 'search' ? <SearchTab /> : <DashboardTab />}</main>
    </div>
  )
}
