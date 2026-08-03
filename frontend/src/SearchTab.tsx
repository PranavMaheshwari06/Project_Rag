import { useState } from 'react'
import { fetchAnswer } from './api'
import type { AnswerResponse } from './types'
import AnswerCard from './components/AnswerCard'
import ChunkCard from './components/ChunkCard'

export default function SearchTab() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnswerResponse | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      setResult(await fetchAnswer(query.trim()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed — is the API running on :8000?')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-tab">
      <form className="search-form" onSubmit={submit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about the docs, e.g. “How do I make a query parameter optional?”"
          aria-label="query"
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Searching…' : 'Ask'}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <>
          <AnswerCard result={result} />
          {result.chunks.length > 0 && (
            <section className="chunks-section">
              <h2>Retrieved chunks</h2>
              {result.chunks.map((rc, i) => {
                const marker = result.citations.find((c) => c.chunk_id === rc.chunk.chunk_id)?.marker
                return <ChunkCard key={rc.chunk.chunk_id} rc={rc} index={i} marker={marker} />
              })}
            </section>
          )}
        </>
      )}
    </div>
  )
}
