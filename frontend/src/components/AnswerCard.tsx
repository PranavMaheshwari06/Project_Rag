import type { AnswerResponse } from '../types'

// renders the answer text with [n] markers as clickable links to the chunk cards
function AnswerText({ text }: { text: string }) {
  const parts = text.split(/(\[\d+\])/g)
  return (
    <p className="answer-text">
      {parts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/)
        if (!m) return <span key={i}>{part}</span>
        return (
          <a key={i} className="citation-marker" href={`#cited-${m[1]}`}>
            {part}
          </a>
        )
      })}
    </p>
  )
}

export default function AnswerCard({ result }: { result: AnswerResponse }) {
  const total = result.latency_ms.total ?? 0

  if (result.refused) {
    return (
      <section className="answer-card refused">
        <div className="answer-meta">
          <span className="badge badge-refused">no grounded answer</span>
          <span className="badge badge-latency">{total.toFixed(0)} ms</span>
        </div>
        <p className="answer-text">{result.answer}</p>
        <p className="refusal-note">
          The best reranked chunk scored below the refusal threshold, so the system declines rather
          than guessing.
        </p>
      </section>
    )
  }

  return (
    <section className="answer-card">
      <div className="answer-meta">
        <span className="badge badge-mode">{result.mode}</span>
        <span className="badge badge-latency">{total.toFixed(0)} ms</span>
        <span className="badge">{result.citations.length} source{result.citations.length === 1 ? '' : 's'}</span>
      </div>
      <AnswerText text={result.answer} />
      {result.citations.length > 0 && (
        <ul className="citation-list">
          {result.citations.map((c) => (
            <li key={c.marker}>
              [{c.marker}]{' '}
              <a href={c.url} target="_blank" rel="noreferrer">
                {c.title} — {c.section_path}
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
