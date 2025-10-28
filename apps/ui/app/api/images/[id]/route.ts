import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/config'

export async function GET(_req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const r = await fetch(`${API_BASE}/images/${id}`, { cache: 'no-store' })
  const text = await r.text()
  try {
    return new NextResponse(text, { status: r.status, headers: { 'content-type': 'application/json' } })
  } catch {
    return NextResponse.json({ error: 'Bad upstream response' }, { status: 502 })
  }
}
