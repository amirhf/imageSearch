import { Suspense } from 'react'
import HomeClient from '@/components/HomeClient'

export const dynamic = 'force-dynamic'

export default function HomePage() {
  return (
    <Suspense fallback={<div className="text-sm text-neutral-500">Loading…</div>}>
      <HomeClient />
    </Suspense>
  )
}
