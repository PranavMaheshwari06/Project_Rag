import type { RetrievedChunk } from '../types'

function Score({ label, value, digits = 3 }: { label: string; value: number | null; digits?: number }) {
  return (
    <span className="score">
      <span className="score-label">{label}</span>
      <span className="score-value">{value === null ? '—' : value.toFixed(digits)}</span>
    </span>
  )
}

export default function ChunkCard({
  rc,
  index,
  marker,
}: {
  rc: RetrievedChunk
  index: number
  marker?: number
}) {
  return (
    <article className="chunk-card" id={marker ? `cited-${marker}` : undefined}>
      <div className="chunk-head">
        <span className="chunk-rank">#{index + 1}</span>
        {marker && <span className="badge badge-cited">cited [{marker}]</span>}
        <a href={rc.chunk.url} target="_blank" rel="noreferrer" className="chunk-title">
          {rc.chunk.title} — {rc.chunk.section_path}
        </a>
      </div>
      <div className="chunk-scores">
        <Score label="dense" value={rc.dense_score} />
        <Score label="bm25" value={rc.bm25_score} digits={2} />
        <Score label="rrf rank" value={rc.rrf_rank} digits={0} />
        <Score label="rerank" value={rc.rerank_score} />
      </div>
      <pre className="chunk-text">{rc.chunk.text}</pre>
    </article>
  )
}
