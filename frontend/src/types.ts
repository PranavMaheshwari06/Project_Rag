// Mirrors the pydantic schemas on the API side.

export interface Chunk {
  chunk_id: string
  doc_id: string
  source: string
  title: string
  section_path: string
  url: string
  text: string
  token_count: number
}

export interface RetrievedChunk {
  chunk: Chunk
  dense_score: number | null
  bm25_score: number | null
  rrf_score: number | null
  rrf_rank: number | null
  rerank_score: number | null
}

export interface Citation {
  marker: number
  chunk_id: string
  url: string
  title: string
  section_path: string
}

export interface AnswerResponse {
  request_id: string
  query: string
  answer: string
  refused: boolean
  mode: string
  citations: Citation[]
  chunks: RetrievedChunk[]
  latency_ms: Record<string, number>
}

export interface ConfigMetrics {
  name: string
  recall: Record<string, number>
  mrr: number
  ndcg: Record<string, number>
  latency_p50_ms: number
  latency_p95_ms: number
  query_count?: number
}

export interface AnswerMetrics {
  groundedness: number
  unsupported_claim_rate: number
  refusal_rate: number
  method: string
  generation_mode?: string
  refusal_confusion?: Record<string, number | null>
}

export interface BenchmarkResult {
  generated_at: string | null
  status?: string
  gold_size: number
  chunk_count: number
  settings_snapshot: Record<string, string | number>
  configs: ConfigMetrics[]
  answers: AnswerMetrics | null
  total_gold_size?: number
  gold_counts?: Record<string, number>
  reviewer_counts?: Record<string, number>
  retrieval_by_kind?: Record<string, ConfigMetrics[]>
  extraction?: Record<string, {
    programmes: number
    fields: number
    draft_accuracy: number | null
    checker_precision: number | null
    checker_recall: number | null
  }>
  refusal_calibration?: {
    status: string
    selected_threshold: number
    method: string
    selected: {
      true_refusals: number
      refusal_count: number
      false_refusals: number
      answerable_count: number
    }
  }
}
