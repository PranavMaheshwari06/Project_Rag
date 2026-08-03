import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { fetchBenchmark } from './api'
import type { BenchmarkResult } from './types'

const BAR_COLORS = ['#94a3b8', '#64748b', '#3b82f6', '#1d4ed8']

function MetricChart({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <div className="chart-box">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 1]} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v: number) => v.toFixed(3)} />
          <Bar dataKey="value" radius={[3, 3, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function DashboardTab() {
  const [bench, setBench] = useState<BenchmarkResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBenchmark().then(setBench).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="error-box">Could not load benchmark.json: {error}</div>
  if (!bench) return <div className="pending-box">Loading…</div>
  if (!bench.configs.length) {
    return (
      <div className="pending-box">
        <strong>Benchmark pending.</strong> Run <code>make eval</code> to generate{' '}
        <code>frontend/public/benchmark.json</code>, then reload this tab.
      </div>
    )
  }

  const toChart = (get: (c: BenchmarkResult['configs'][number]) => number) =>
    bench.configs.map((c) => ({ name: c.name, value: get(c) }))

  return (
    <div className="dashboard-tab">
      <p className="bench-meta">
        {bench.gold_size} gold questions · {bench.chunk_count} chunks · generated {bench.generated_at}
      </p>

      <table className="bench-table">
        <thead>
          <tr>
            <th>config</th>
            <th>Recall@5</th>
            <th>Recall@10</th>
            <th>MRR</th>
            <th>nDCG@10</th>
            <th>p50 (ms)</th>
            <th>p95 (ms)</th>
          </tr>
        </thead>
        <tbody>
          {bench.configs.map((c) => (
            <tr key={c.name}>
              <td className="config-name">{c.name}</td>
              <td>{(c.recall['@5'] ?? 0).toFixed(3)}</td>
              <td>{(c.recall['@10'] ?? 0).toFixed(3)}</td>
              <td>{c.mrr.toFixed(3)}</td>
              <td>{(c.ndcg['@10'] ?? 0).toFixed(3)}</td>
              <td>{c.latency_p50_ms.toFixed(0)}</td>
              <td>{c.latency_p95_ms.toFixed(0)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="charts-grid">
        <MetricChart title="Recall@10" data={toChart((c) => c.recall['@10'] ?? 0)} />
        <MetricChart title="MRR" data={toChart((c) => c.mrr)} />
        <MetricChart title="nDCG@10" data={toChart((c) => c.ndcg['@10'] ?? 0)} />
      </div>

      <div className="chart-box">
        <h3>Latency (ms)</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={bench.configs.map((c) => ({ name: c.name, p50: c.latency_p50_ms, p95: c.latency_p95_ms }))}
            margin={{ top: 4, right: 8, left: -8, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="p50" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            <Bar dataKey="p95" fill="#94a3b8" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {bench.answers && (
        <div className="answer-metrics">
          <h3>Answer quality (hybrid + rerank)</h3>
          <div className="metric-cards">
            <div className="metric-card">
              <span className="metric-value">{(bench.answers.groundedness * 100).toFixed(1)}%</span>
              <span className="metric-label">groundedness</span>
            </div>
            <div className="metric-card">
              <span className="metric-value">{(bench.answers.unsupported_claim_rate * 100).toFixed(1)}%</span>
              <span className="metric-label">unsupported claims</span>
            </div>
            <div className="metric-card">
              <span className="metric-value">{(bench.answers.refusal_rate * 100).toFixed(1)}%</span>
              <span className="metric-label">refusal rate</span>
            </div>
          </div>
          <p className="method-note">method: {bench.answers.method}</p>
        </div>
      )}
    </div>
  )
}
