import { NextRequest, NextResponse } from 'next/server'
import { API_BASE as API_BASE_FROM_CFG } from '@/lib/config'
import { parsePrometheusText, histogramQuantile, sumMetric } from '@/lib/utils/prometheus'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest) {
  try {
    const base = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, '') || API_BASE_FROM_CFG
    if (!base || base.startsWith('http://localhost')) {
      return NextResponse.json(
        { error: 'API base not configured for production', hint: 'Set NEXT_PUBLIC_API_BASE to your Cloud Run URL' },
        { status: 500 }
      )
    }

    const upstream = `${base}/metrics`
    const r = await fetch(upstream, { cache: 'no-store', headers: { accept: 'text/plain' } })
    const text = await r.text()
    if (!r.ok) {
      return NextResponse.json(
        { error: 'Upstream metrics fetch failed', status: r.status, upstream },
        { status: 502 }
      )
    }
    const samples = parsePrometheusText(text)

    // Latency quantiles from histogram buckets (best-effort name detection)
    const bucketNames = [
      'request_latency_ms_bucket',
      'http_request_duration_ms_bucket',
      'request_duration_ms_bucket'
    ]
    let p50: number | null = null
    let p95: number | null = null
    for (const name of bucketNames) {
      const q50 = histogramQuantile(samples, name, 0.5)
      const q95 = histogramQuantile(samples, name, 0.95)
      if (q50 != null || q95 != null) {
        p50 = q50
        p95 = q95
        break
      }
    }

    // Route split counts
    const localCount = Math.round(sumMetric(samples, 'router_local_total'))
    const cloudCount = Math.round(sumMetric(samples, 'router_cloud_total'))
    const totalCount = localCount + cloudCount

    // Cost and cache (best-effort metric names)
    const estCost = sumMetric(samples, 'cost_usd_total') || null
    const cacheHit = sumMetric(samples, 'cache_hit_total') || sumMetric(samples, 'cache_hits_total') || null

    return NextResponse.json({
      p50,
      p95,
      local_count: localCount,
      cloud_count: cloudCount,
      total_count: totalCount,
      est_cost_usd: estCost,
      cache_hit: cacheHit
    })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Metrics parse error' }, { status: 500 })
  }
}
