import { NextRequest, NextResponse } from 'next/server'
import { API_BASE } from '@/lib/config'

export async function GET(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  
  // Forward authorization header if present
  const authHeader = req.headers.get('authorization')
  const headers: HeadersInit = {}
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  
  const r = await fetch(`${API_BASE}/images/${id}`, { cache: 'no-store', headers })
  const text = await r.text()
  try {
    return new NextResponse(text, { status: r.status, headers: { 'content-type': 'application/json' } })
  } catch {
    return NextResponse.json({ error: 'Bad upstream response' }, { status: 502 })
  }
}

export async function PATCH(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  
  // Forward authorization header
  const authHeader = req.headers.get('authorization')
  const headers: HeadersInit = {
    'Content-Type': 'application/json'
  }
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  
  const body = await req.text()
  const r = await fetch(`${API_BASE}/images/${id}`, { 
    method: 'PATCH', 
    body,
    headers 
  })
  const text = await r.text()
  try {
    return new NextResponse(text, { status: r.status, headers: { 'content-type': 'application/json' } })
  } catch {
    return NextResponse.json({ error: 'Bad upstream response' }, { status: 502 })
  }
}

export async function DELETE(req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  
  // Forward authorization header
  const authHeader = req.headers.get('authorization')
  const headers: HeadersInit = {}
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  
  const r = await fetch(`${API_BASE}/images/${id}`, { 
    method: 'DELETE',
    headers 
  })
  const text = await r.text()
  try {
    return new NextResponse(text, { status: r.status, headers: { 'content-type': 'application/json' } })
  } catch {
    return NextResponse.json({ error: 'Bad upstream response' }, { status: 502 })
  }
}
