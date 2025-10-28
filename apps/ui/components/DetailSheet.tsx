"use client"

import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getImage } from '@/lib/api'

export default function DetailSheet({ id, onClose }: { id: string | null; onClose: () => void }) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    if (id) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [id, onClose])

  if (!id) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-10 mx-4 w-full max-w-4xl overflow-hidden rounded-lg bg-white shadow-xl">
        <Panel id={id} onClose={onClose} />
      </div>
    </div>
  )
}

function Panel({ id, onClose }: { id: string; onClose: () => void }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['image', id],
    queryFn: () => getImage(id),
    staleTime: 60_000
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-2">
      <div className="bg-neutral-50 p-4">
        {isLoading ? (
          <div className="aspect-square animate-pulse rounded-md bg-neutral-200" />
        ) : isError || !data ? (
          <div className="text-sm text-red-600">Failed to load image</div>
        ) : (
          <img
            src={data.download_url || data.thumbnail_url}
            alt={data.caption || 'image'}
            className="mx-auto max-h-[70vh] rounded-md object-contain"
          />
        )}
      </div>
      <div className="space-y-4 p-4">
        <div className="flex items-start justify-between">
          <h2 className="text-lg font-semibold">Image Details</h2>
          <button onClick={onClose} className="rounded-md border px-3 py-1 text-sm hover:bg-neutral-50">Close</button>
        </div>
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-4 w-2/3 animate-pulse rounded bg-neutral-200" />
            <div className="h-4 w-1/2 animate-pulse rounded bg-neutral-200" />
          </div>
        ) : data ? (
          <div className="space-y-3">
            <div>
              <div className="text-xs uppercase text-neutral-500">Caption</div>
              <div className="text-sm text-neutral-800">{data.caption}</div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {data.width && <div><span className="text-neutral-500">Width:</span> {data.width}px</div>}
              {data.height && <div><span className="text-neutral-500">Height:</span> {data.height}px</div>}
              {data.format && <div><span className="text-neutral-500">Format:</span> {data.format}</div>}
              {typeof data.caption_confidence === 'number' && (
                <div><span className="text-neutral-500">Confidence:</span> {data.caption_confidence.toFixed(2)}</div>
              )}
            </div>
            <div className="pt-2">
              <button
                className="rounded-md bg-neutral-900 px-3 py-2 text-sm text-white hover:bg-neutral-800"
                onClick={() => {
                  const q = data.caption || ''
                  if (q) window.location.href = `/?q=${encodeURIComponent(q)}`
                }}
                aria-label="Find similar"
              >
                Find similar
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
