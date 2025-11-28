"use client"

import { useState, useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import SearchBar from '@/components/SearchBar'
import ImageMasonry from '@/components/ImageMasonry'
import DetailSheet from '@/components/DetailSheet'
import { searchImages } from '@/lib/api'

import { useAuth } from '@/lib/auth/AuthContext'

export default function HomeClient() {
  const { user, session } = useAuth()
  const sp = useSearchParams()
  const q = sp.get('q') || ''
  const k = Number(sp.get('k') || '10')

  const scope = user ? 'all' : 'public'

  const enabled = q.trim().length > 0
  const { data, isFetching, isError } = useQuery({
    queryKey: ['search', q, k, scope, session?.access_token],
    queryFn: () => searchImages(q, k, scope, session?.access_token),
    enabled
  })

  const items = useMemo(() => data?.results ?? [], [data])

  const [openId, setOpenId] = useState<string | null>(null)

  return (
    <main className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Gallery</h1>
      </div>

      <SearchBar />

      {!enabled && (
        <div className="rounded-md border border-dashed p-6 text-neutral-600">
          Enter a search query (e.g., <em>beach at sunset</em>) and press Search.
        </div>
      )}

      {isError && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-red-700">Search failed.</div>
      )}

      {enabled && (
        <div className="space-y-3">
          {isFetching && <div className="text-sm text-neutral-500">Loading…</div>}
          <ImageMasonry items={items} onOpen={setOpenId} />
        </div>
      )}

      <DetailSheet id={openId} onClose={() => setOpenId(null)} />
    </main>
  )
}
