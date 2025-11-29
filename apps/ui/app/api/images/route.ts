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
    // Forward headers
    const headers: HeadersInit = {}

    // 1. Auth
    const authHeader = req.headers.get('authorization')
    if (authHeader) headers['Authorization'] = authHeader

    // 2. Content-Type (preserve boundary for multipart)
    const contentType = req.headers.get('content-type')
    if (contentType) headers['Content-Type'] = contentType

    // 3. Client Caption Headers
    const clientCaption = req.headers.get('x-client-caption')
    const clientConfidence = req.headers.get('x-client-confidence')
    if (clientCaption) headers['x-client-caption'] = clientCaption
    if (clientConfidence) headers['x-client-confidence'] = clientConfidence

    // 4. Stream body directly to upstream
    // @ts-ignore - duplex is required for streaming bodies in node fetch but TS might complain
    const upstream = await fetch(`${API_BASE}/images`, {
      method: 'POST',
      body: req.body,
      headers,
      duplex: 'half'
    })

    const text = await upstream.text()
    return new NextResponse(text, { status: upstream.status, headers: { 'content-type': 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Upload failed' }, { status: 500 })
  }
}
