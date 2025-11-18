'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function ImagePage() {
  const params = useParams()
  const id = params.id as string
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadImage() {
      try {
        setLoading(true)
        setError(null)
        
        // Get auth token
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()
        const token = session?.access_token
        
        const headers: HeadersInit = {}
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
        
        const r = await fetch(`/api/images/${id}`, { 
          cache: 'no-store',
          headers 
        })
        
        if (!r.ok) {
          throw new Error(`Failed to load image: ${r.status}`)
        }
        
        const imageData = await r.json()
        setData(imageData)
      } catch (err: any) {
        setError(err.message || 'Failed to load image')
      } finally {
        setLoading(false)
      }
    }
    
    loadImage()
  }, [id])

  if (loading) {
    return (
      <main className="space-y-6">
        <div className="text-center py-12">
          <div className="text-neutral-600">Loading...</div>
        </div>
      </main>
    )
  }

  if (error || !data) {
    return (
      <main className="space-y-6">
        <div className="text-center py-12">
          <div className="text-red-600">{error || 'Image not found'}</div>
          <a href="/" className="text-sm text-blue-600 hover:underline mt-4 inline-block">
            Back to search
          </a>
        </div>
      </main>
    )
  }

  return (
    <main className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Image detail</h1>
        <a href="/" className="text-sm text-neutral-600 hover:underline">Back to search</a>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-md bg-neutral-50 p-4">
          <img
            src={data.download_url || data.thumbnail_url}
            alt={data.caption || 'image'}
            className="mx-auto max-h-[70vh] rounded-md object-contain"
          />
        </div>
        <div className="space-y-4">
          <div>
            <div className="text-xs uppercase text-neutral-500">Caption</div>
            <div className="text-sm text-neutral-800">{data.caption}</div>
            <div className="text-xs text-neutral-500">
              {data.caption_origin ? (<span>Origin: {data.caption_origin}</span>) : null}
              {typeof data.caption_confidence === 'number' ? (
                <span> • Confidence: {data.caption_confidence.toFixed(2)}</span>
              ) : null}
            </div>
          </div>
          {(data.caption_local || data.caption_cloud) && (
            <div className="rounded-md border p-3">
              <div className="text-xs uppercase text-neutral-500 mb-2">Captions (local/cloud)</div>
              {data.caption_local && (
                <div className="mb-2">
                  <div className="text-[11px] text-blue-700">Local</div>
                  <div className="text-sm">{data.caption_local}</div>
                </div>
              )}
              {data.caption_cloud && (
                <div>
                  <div className="text-[11px] text-violet-700">Cloud</div>
                  <div className="text-sm">{data.caption_cloud}</div>
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-sm">
            {data.width && <div><span className="text-neutral-500">Width:</span> {data.width}px</div>}
            {data.height && <div><span className="text-neutral-500">Height:</span> {data.height}px</div>}
            {data.format && <div><span className="text-neutral-500">Format:</span> {data.format}</div>}
            {data.size_bytes && <div><span className="text-neutral-500">Size:</span> {(data.size_bytes/1024).toFixed(1)} KB</div>}
          </div>

          <div className="pt-2">
            <a
              className="inline-block rounded-md bg-neutral-900 px-3 py-2 text-sm text-white hover:bg-neutral-800"
              href={`/?q=${encodeURIComponent(data.caption || '')}`}
            >
              Find similar
            </a>
          </div>
        </div>
      </div>
    </main>
  )
}
