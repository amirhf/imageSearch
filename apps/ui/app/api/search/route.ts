import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/config'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const q = searchParams.get('q')
  const k = searchParams.get('k') ?? '10'
  const scope = searchParams.get('scope') ?? 'public'
  if (!q) return NextResponse.json({ error: 'Missing q' }, { status: 400 })

  // Forward authorization header if present
  const authHeader = req.headers.get('authorization')
  const headers: HeadersInit = {}
  if (authHeader) {
    headers['Authorization'] = authHeader
  }

  const upstream = `${API_BASE}/search?q=${encodeURIComponent(q)}&k=${encodeURIComponent(k)}&scope=${encodeURIComponent(scope)}`
  const r = await fetch(upstream, { cache: 'no-store', headers })
  const text = await r.text()
  try {
    return new NextResponse(text, { status: r.status, headers: { 'content-type': 'application/json' } })
  } catch {
    return NextResponse.json({ error: 'Bad upstream response' }, { status: 502 })
  }
}
