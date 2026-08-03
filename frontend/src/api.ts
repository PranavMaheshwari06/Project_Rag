import type { AnswerResponse, BenchmarkResult } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export async function fetchAnswer(query: string): Promise<AnswerResponse> {
  const resp = await fetch(`${API_BASE}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null)
    throw new Error(detail?.detail ?? `API error ${resp.status}`)
  }
  return resp.json()
}

// served from the frontend's own public dir, so the dashboard works with no backend
export async function fetchBenchmark(): Promise<BenchmarkResult> {
  const resp = await fetch('/benchmark.json')
  if (!resp.ok) throw new Error('benchmark.json not found')
  return resp.json()
}
