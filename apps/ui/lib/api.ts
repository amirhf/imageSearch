import { ImageDetail, SearchResponse } from './types'

export async function searchImages(q: string, k = 10, scope = 'public', token?: string): Promise<SearchResponse> {
  const url = new URL('/api/search', typeof window === 'undefined' ? 'http://localhost' : window.location.origin)
  url.searchParams.set('q', q)
  url.searchParams.set('k', String(k))
  url.searchParams.set('scope', scope)

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url.toString(), { cache: 'no-store', headers })
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function getImage(id: string): Promise<ImageDetail> {
  const res = await fetch(`/api/images/${id}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Image fetch failed: ${res.status}`)
  return res.json()
}

import { API_BASE } from './config'

export async function uploadImage(
  input: { url?: string; file?: File; visibility?: string; edgeCaption?: { text: string; score: number } },
  token?: string
): Promise<ImageDetail> {
  const form = new FormData()
  if (input.url) form.set('url', input.url)
  if (input.file) form.set('file', input.file, input.file.name)
  if (input.visibility) form.set('visibility', input.visibility)
  if (!form.has('url') && !form.has('file')) throw new Error('Provide url or file')

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // Add Edge Caption headers if available
  if (input.edgeCaption) {
    headers['x-client-caption'] = input.edgeCaption.text.replace(/[\r\n]+/g, ' ').trim()
    headers['x-client-confidence'] = input.edgeCaption.score.toString()
  }

  // Upload directly to backend to bypass Vercel 4.5MB limit
  const uploadUrl = `${API_BASE}/images`
  console.log('[DEBUG] Uploading to:', uploadUrl)

  const res = await fetch(uploadUrl, {
    method: 'POST',
    body: form,
    headers
  })

  if (res.status === 401) {
    throw new Error('Authentication required. Please log in.')
  }
  if (res.status === 403) {
    throw new Error('You do not have permission to perform this action')
  }
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Upload failed: ${res.status} ${err}`)
  }

  return res.json()
}

export async function uploadImageAsync(
  input: { url?: string; file?: File; visibility?: string; edgeCaption?: { text: string; score: number } },
  token?: string,
  priority: 'low' | 'normal' | 'high' = 'normal'
): Promise<{ job_id: string; status: string; poll_url: string }> {
  const form = new FormData()
  if (input.url) form.set('url', input.url)
  if (input.file) form.set('file', input.file, input.file.name)
  if (input.visibility) form.set('visibility', input.visibility)

  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // Add Edge Caption headers if available
  if (input.edgeCaption) {
    headers['x-client-caption'] = input.edgeCaption.text.replace(/[\r\n]+/g, ' ').trim()
    headers['x-client-confidence'] = input.edgeCaption.score.toString()
  }

  const uploadUrl = `${API_BASE}/images/async?priority=${priority}`
  console.log('[DEBUG] Async uploading to:', uploadUrl)

  const res = await fetch(uploadUrl, {
    method: 'POST',
    body: form,
    headers
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Async upload failed: ${res.status} ${err}`)
  }

  return res.json()
}

export async function getJobStatus(jobId: string, token?: string): Promise<{ status: string; result?: any; error?: string }> {
  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}/jobs/${jobId}`, { headers, cache: 'no-store' })
  if (!res.ok) throw new Error(`Job poll failed: ${res.status}`)
  return res.json()
}
