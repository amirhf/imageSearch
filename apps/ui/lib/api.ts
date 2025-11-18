import { ImageDetail, SearchResponse } from './types'

export async function searchImages(q: string, k = 10): Promise<SearchResponse> {
  const url = new URL('/api/search', typeof window === 'undefined' ? 'http://localhost' : window.location.origin)
  url.searchParams.set('q', q)
  url.searchParams.set('k', String(k))
  const res = await fetch(url.toString(), { cache: 'no-store' })
  if (!res.ok) throw new Error(`Search failed: ${res.status}`)
  return res.json()
}

export async function getImage(id: string): Promise<ImageDetail> {
  const res = await fetch(`/api/images/${id}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`Image fetch failed: ${res.status}`)
  return res.json()
}

export async function uploadImage(
  input: { url?: string; file?: File; visibility?: string },
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
  
  const res = await fetch('/api/images', { 
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
    throw new Error(`Upload failed: ${res.status}`)
  }
  
  return res.json()
}
