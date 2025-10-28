'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useState, useEffect } from 'react'

export default function SearchBar() {
  const router = useRouter()
  const sp = useSearchParams()
  const [q, setQ] = useState(sp.get('q') ?? '')
  const [k, setK] = useState(sp.get('k') ?? '10')

  useEffect(() => {
    setQ(sp.get('q') ?? '')
    setK(sp.get('k') ?? '10')
  }, [sp])

  function submit(e?: React.FormEvent) {
    e?.preventDefault()
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    if (k) params.set('k', k)
    router.push(`/?${params.toString()}`)
  }

  return (
    <form onSubmit={submit} className="flex flex-wrap items-center gap-2">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search images…"
        className="flex-1 min-w-[220px] rounded-md border border-neutral-300 bg-white px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-400"
        aria-label="Search query"
      />
      <input
        value={k}
        onChange={(e) => setK(e.target.value)}
        type="number"
        min={1}
        max={100}
        className="w-20 rounded-md border border-neutral-300 bg-white px-3 py-2 shadow-sm focus:outline-none"
        aria-label="Top K"
        title="Top K"
      />
      <button
        type="submit"
        className="rounded-md bg-neutral-900 px-4 py-2 text-white hover:bg-neutral-800"
        aria-label="Submit search"
      >
        Search
      </button>
    </form>
  )
}
