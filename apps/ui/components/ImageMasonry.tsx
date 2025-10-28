import { ImageSummary } from '@/lib/types'
import { ImageCard } from './ImageCard'

export default function ImageMasonry({ items, onOpen }: { items: ImageSummary[]; onOpen?: (id: string) => void }) {
  if (!items?.length) {
    return <div className="text-neutral-500">No results</div>
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {items.map((it) => (
        <ImageCard key={it.id} item={it} onOpen={onOpen} />
      ))}
    </div>
  )
}
