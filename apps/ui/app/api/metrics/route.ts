import { NextResponse } from 'next/server'
import { API_BASE } from '@/lib/config'
import { parsePrometheusText } from '@/lib/metrics'

export async function GET() {
  try {
    const r = await fetch(`${API_BASE}/metrics`, { cache: 'no-store' })
    const text = await r.text()
    if (!r.ok) {
      return NextResponse.json({ error: 'Failed to fetch metrics' }, { status: r.status })
    }
    const parsed = parsePrometheusText(text)
    return NextResponse.json(parsed)
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Metrics fetch failed' }, { status: 500 })
  }
}
