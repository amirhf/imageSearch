import { headers } from 'next/headers'
import MetricStat from '@/components/metrics/MetricStat'
import RouteSplitDial from '@/components/metrics/RouteSplitDial'

async function getSummary() {
  const h = await headers()
  const host = h.get('x-forwarded-host') ?? h.get('host')
  const proto = h.get('x-forwarded-proto') ?? 'http'
  if (!host) throw new Error('Missing host header')
  const base = `${proto}://${host}`
  const r = await fetch(`${base}/api/metrics/summary`, { cache: 'no-store' })
  if (!r.ok) throw new Error('Failed to load metrics')
  return r.json()
}

export const dynamic = 'force-dynamic'

export default async function MetricsPage() {
  const data = await getSummary()
  const { p50, p95, local_count, cloud_count, total_count, est_cost_usd, cache_hit } = data || {}
  return (
    <main className="space-y-6">
      <h1 className="text-xl font-semibold">Metrics</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricStat label="p50 latency" value={p50 != null ? Math.round(p50) : null} suffix="ms" />
        <MetricStat label="p95 latency" value={p95 != null ? Math.round(p95) : null} suffix="ms" />
        <MetricStat label="Requests" value={total_count ?? null} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <RouteSplitDial local={local_count ?? 0} cloud={cloud_count ?? 0} />
        <div className="grid grid-cols-1 gap-4">
          <MetricStat label="Estimated cost" value={est_cost_usd != null ? `$${est_cost_usd.toFixed(4)}` : null} />
          <MetricStat label="Cache hits" value={cache_hit ?? null} />
        </div>
      </div>
    </main>
  )
}
