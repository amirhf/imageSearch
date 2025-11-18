import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/config'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    
    // Forward authorization header if present
    const authHeader = req.headers.get('authorization')
    const headers: HeadersInit = {}
    if (authHeader) {
      headers['Authorization'] = authHeader
    }

    const upstream = `${API_BASE}/images?${searchParams.toString()}`
    const r = await fetch(upstream, { cache: 'no-store', headers })
    const text = await r.text()
    return new NextResponse(text, { status: r.status, headers: { 'content-type': 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Failed to fetch images' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const form = await req.formData()
    const out = new FormData()
    const url = form.get('url')
    const file = form.get('file')
    const visibility = form.get('visibility')

    if (typeof url === 'string' && url.trim().length > 0) {
      out.set('url', url.trim())
    }
    if (file instanceof File) {
      out.set('file', file, file.name)
    }
    if (typeof visibility === 'string') {
      out.set('visibility', visibility)
    }

    if (!out.has('url') && !out.has('file')) {
      return NextResponse.json({ error: 'Provide either url or file' }, { status: 400 })
    }

    // Forward authorization header
    const authHeader = req.headers.get('authorization')
    const headers: HeadersInit = {}
    if (authHeader) {
      headers['Authorization'] = authHeader
    }

    const upstream = await fetch(`${API_BASE}/images`, { method: 'POST', body: out, headers })
    const text = await upstream.text()
    return new NextResponse(text, { status: upstream.status, headers: { 'content-type': 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Upload failed' }, { status: 500 })
  }
}
