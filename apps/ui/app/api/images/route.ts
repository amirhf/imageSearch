import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/config'

export async function POST(req: NextRequest) {
  try {
    const form = await req.formData()
    const out = new FormData()
    const url = form.get('url')
    const file = form.get('file')

    if (typeof url === 'string' && url.trim().length > 0) {
      out.set('url', url.trim())
    }
    if (file instanceof File) {
      out.set('file', file, file.name)
    }

    if (!out.has('url') && !out.has('file')) {
      return NextResponse.json({ error: 'Provide either url or file' }, { status: 400 })
    }

    const upstream = await fetch(`${API_BASE}/images`, { method: 'POST', body: out })
    const text = await upstream.text()
    return new NextResponse(text, { status: upstream.status, headers: { 'content-type': 'application/json' } })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || 'Upload failed' }, { status: 500 })
  }
}
